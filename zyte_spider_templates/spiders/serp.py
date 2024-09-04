from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Union
from urllib.parse import urlparse, urlunparse

import scrapy
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy.settings import SETTINGS_PRIORITIES, BaseSettings
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Serp

from zyte_spider_templates.params import parse_input_params

from ..params import (
    INPUT_GROUP_FIELDS,
    URL_FIELD_KWARGS,
    URLS_FIELD_KWARGS,
    URLS_FILE_FIELD_KWARGS,
    MaxRequestsParam,
    validate_url_list,
)
from .base import INPUT_GROUP, BaseSpider


class SearchKeywordsParam(BaseModel):
    search_keywords: Optional[List[str]] = Field(
        title="Search Keywords",
        description=("Search keywords to use on the specified input Google URLs."),
        json_schema_extra={
            "widget": "textarea",
        },
    )

    @field_validator("search_keywords", mode="before")
    @classmethod
    def validate_search_keywords(cls, value: Union[List[str], str]) -> List[str]:
        """Validate a list of search keywords.
        If a string is received as input, it is split into multiple strings
        on new lines.
        """
        if isinstance(value, str):
            value = value.split("\n")
        if not value:
            raise ValueError("The search_keywords parameter value is missing or empty.")
        result = []
        for v in value:
            if not (v := v.strip()):
                continue
            result.append(v)
        return result


class SerpMaxPagesParam(BaseModel):
    max_pages: int = Field(
        title="Pages",
        description="Maximum number of result pages to visit per input URL.",
        default=1,
    )


GOOGLE_URL_FIELD_KWARGS = deepcopy(URL_FIELD_KWARGS)
GOOGLE_URL_FIELD_KWARGS["default"] = "https://www.google.com/"
GOOGLE_URL_FIELD_KWARGS[
    "description"
] = "Target Google URL. Defaults to https://www.google.com/."


class GoogleUrlParam(BaseModel):
    url: str = Field(**GOOGLE_URL_FIELD_KWARGS)  # type: ignore[misc, arg-type]


GOOGLE_URLS_FIELD_KWARGS = deepcopy(URLS_FIELD_KWARGS)
GOOGLE_URLS_FIELD_KWARGS[
    "description"
] = "Target Google URLs. Defaults to https://www.google.com/."


class GoogleUrlsParam(BaseModel):
    urls: Optional[List[str]] = Field(**GOOGLE_URLS_FIELD_KWARGS)  # type: ignore[misc, arg-type]

    @field_validator("urls", mode="before")
    @classmethod
    def validate_url_list(cls, value: Union[List[str], str]) -> List[str]:
        return validate_url_list(value)


GOOGLE_URLS_FILE_FIELD_KWARGS = deepcopy(URLS_FILE_FIELD_KWARGS)
GOOGLE_URLS_FILE_FIELD_KWARGS["description"] = (
    "URL that point to a plain-text file with a list of target Google URLs, "
    "e.g. https://example.com/url-list.txt. The linked list must contain 1 "
    "Google URL (e.g. https://www.google.com/) per line."
)


class GoogleUrlsFileParam(BaseModel):
    urls_file: str = Field(**GOOGLE_URLS_FILE_FIELD_KWARGS)  # type: ignore[misc, arg-type]


class GoogleSearchSpiderParams(
    MaxRequestsParam,
    SerpMaxPagesParam,
    SearchKeywordsParam,
    GoogleUrlsFileParam,
    GoogleUrlsParam,
    GoogleUrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        # https://github.com/pydantic/pydantic/discussions/7763#discussioncomment-10338857
        protected_namespaces=(),
        json_schema_extra={
            "groups": [
                INPUT_GROUP,
            ],
        },
    )

    @model_validator(mode="after")
    def input_group(self):
        input_fields = set(
            field for field in INPUT_GROUP_FIELDS if getattr(self, field, None)
        )
        if not input_fields:
            input_field_list = ", ".join(INPUT_GROUP_FIELDS)
            raise ValueError(
                f"No input parameter defined. Please, define one of: "
                f"{input_field_list}."
            )
        elif (
            len(input_fields) > 1
            and getattr(self, "url", None) != GOOGLE_URL_FIELD_KWARGS["default"]
        ):
            input_field_list = ", ".join(
                f"{field} ({getattr(self, field)!r})" for field in input_fields
            )
            raise ValueError(
                f"Expected a single input parameter, got {len(input_fields)}: "
                f"{input_field_list}."
            )
        return self


class GoogleSearchSpider(Args[GoogleSearchSpiderParams], BaseSpider):
    """Yield results from Google searches.

    See :class:`~zyte_spider_templates.spiders.serp.GoogleSearchSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`google-search`.
    """

    name = "google_search"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "Google Search Results",
        "description": "Template for spiders that extract Google search results.",
    }

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        retry_policy_setting_priority = settings.getpriority("ZYTE_API_RETRY_POLICY")
        if (
            retry_policy_setting_priority is None
            or retry_policy_setting_priority < SETTINGS_PRIORITIES["spider"]
        ):
            settings.set(
                "ZYTE_API_RETRY_POLICY",
                "zyte_api.aggressive_retrying",
                priority="spider",
            )

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> scrapy.Spider:
        spider = super().from_crawler(crawler, *args, **kwargs)
        parse_input_params(spider)
        return spider

    def get_start_request(self, url):
        return Request(
            url=url,
            callback=self.parse_serp,
            meta={
                "crawling_logs": {"page_type": "serp"},
                "zyte_api": {
                    "serp": True,
                },
            },
        )

    def start_requests(self) -> Iterable[Request]:
        search_keywords = self.args.search_keywords
        if not search_keywords:
            raise ValueError("No search keywords specified.")

        for url in self.start_urls:
            url = urlunparse(urlparse(url)._replace(path="/search"))
            for search_keyword in search_keywords:
                search_url = add_or_replace_parameter(url, "q", search_keyword)
                for start in range(0, self.args.max_pages * 10, 10):
                    if start:
                        search_url = add_or_replace_parameter(
                            search_url, "start", str(start)
                        )
                    yield self.get_start_request(search_url)

    def parse_serp(self, response) -> Iterable[Serp]:
        yield Serp.from_dict(response.raw_api_response["serp"])
