from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from scrapy import Request
from scrapy.settings import SETTINGS_PRIORITIES, BaseSettings
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Serp

from ..params import MaxRequestsParam
from ._google_domains import GoogleDomain
from .base import BaseSpider


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


class GoogleDomainParam(BaseModel):
    domain: GoogleDomain = Field(
        title="Domain",
        description="Target Google domain.",
        default=GoogleDomain.google_com,
    )


class GoogleSearchSpiderParams(
    MaxRequestsParam,
    SerpMaxPagesParam,
    SearchKeywordsParam,
    GoogleDomainParam,
    BaseModel,
):
    pass


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

        url = f"https://www.{self.args.domain.value}/search"
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
