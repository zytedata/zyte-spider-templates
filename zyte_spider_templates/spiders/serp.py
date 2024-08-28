from copy import deepcopy
from typing import Any, Dict, Iterable, List, Optional, Union

import scrapy
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Serp

from zyte_spider_templates.params import parse_input_params
from zyte_spider_templates.spiders.base import BaseSpider

from ..params import (
    URL_FIELD_KWARGS,
    URLS_FIELD_KWARGS,
    MaxRequestsParam,
    UrlsFileParam,
    validate_url_list,
)
from .base import _INPUT_FIELDS


class SerpMaxPagesParam(BaseModel):
    max_pages: int = Field(
        title="Pages",
        description="Maximum number of result pages to visit per input URL.",
        default=1,
    )


SERP_URL_FIELD_KWARGS = deepcopy(URL_FIELD_KWARGS)
assert isinstance(SERP_URL_FIELD_KWARGS["description"], str)
SERP_URL_FIELD_KWARGS["description"] = SERP_URL_FIELD_KWARGS["description"].replace(
    "https://toscrape.com/", "https://google.com/search?q=foo+bar"
)


class SerpUrlParam(BaseModel):
    url: str = Field(**SERP_URL_FIELD_KWARGS)  # type: ignore[misc, arg-type]


SERP_URLS_FIELD_KWARGS = deepcopy(URLS_FIELD_KWARGS)
assert isinstance(SERP_URLS_FIELD_KWARGS["description"], str)
SERP_URLS_FIELD_KWARGS["description"] = SERP_URLS_FIELD_KWARGS["description"].replace(
    "https://toscrape.com/", "https://google.com/search?q=foo+bar"
)


class SerpUrlsParam(BaseModel):
    urls: Optional[List[str]] = Field(**SERP_URLS_FIELD_KWARGS)  # type: ignore[misc, arg-type]

    @field_validator("urls", mode="before")
    @classmethod
    def validate_url_list(cls, value: Union[List[str], str]) -> List[str]:
        return validate_url_list(value)


class SerpSpiderParams(
    MaxRequestsParam,
    SerpMaxPagesParam,
    UrlsFileParam,
    SerpUrlsParam,
    SerpUrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        # https://github.com/pydantic/pydantic/discussions/7763#discussioncomment-10338857
        protected_namespaces=(),
        json_schema_extra={
            "groups": [
                {
                    "id": "inputs",
                    "title": "Inputs",
                    "description": (
                        "Input data that determines the start URLs of the crawl."
                    ),
                    "widget": "exclusive",
                },
            ],
        },
    )

    @model_validator(mode="after")
    def single_input(self):
        """Fields
        :class:`~zyte_spider_templates.spiders.serp.SerpSpiderParams.url`
        and
        :class:`~zyte_spider_templates.spiders.serp.SerpSpiderParams.urls_file`
        form a mandatory, mutually-exclusive field group: one of them must be
        defined, the rest must not be defined."""
        input_fields = set(
            field for field in _INPUT_FIELDS if getattr(self, field, None)
        )
        if not input_fields:
            input_field_list = ", ".join(_INPUT_FIELDS)
            raise ValueError(
                f"No input parameter defined. Please, define one of: "
                f"{input_field_list}."
            )
        elif len(input_fields) > 1:
            input_field_list = ", ".join(
                f"{field} ({getattr(self, field)!r})" for field in input_fields
            )
            raise ValueError(
                f"Expected a single input parameter, got {len(input_fields)}: "
                f"{input_field_list}."
            )
        return self


class SerpSpider(Args[SerpSpiderParams], BaseSpider):
    """Yield results from search engine result pages (SERP).

    See :class:`~zyte_spider_templates.spiders.serp.SerpSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`serp`.
    """

    name = "serp"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "SERP",
        "description": "Template for spiders that extract Google search results.",
    }

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
        for url in self.start_urls:
            for start in range(0, self.args.max_pages * 10, 10):
                if start:
                    url = add_or_replace_parameter(url, "start", str(start))
                yield self.get_start_request(url)

    def parse_serp(self, response) -> Iterable[Serp]:
        yield Serp.from_dict(response.raw_api_response["serp"])
