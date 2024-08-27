from typing import Any, Dict, Iterable

import requests
import scrapy
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Serp

from zyte_spider_templates.spiders.base import BaseSpider
from zyte_spider_templates.utils import get_domain

from ..params import MaxRequestsParam, UrlParam, UrlsFileParam, UrlsParam
from ..utils import load_url_list
from .base import _INPUT_FIELDS


class SerpMaxPagesParam(BaseModel):
    max_pages: int = Field(
        title="Pages",
        description="Maximum number of result pages to visit per input URL.",
        default=1,
    )


class SerpSpiderParams(
    MaxRequestsParam,
    SerpMaxPagesParam,
    UrlsFileParam,
    UrlsParam,
    UrlParam,
    BaseModel,
):
    model_config = ConfigDict(
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
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.url`
        and
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.urls_file`
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

    See :class:`~zyte_spider_templates.spiders.ecommerce.SerpSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`serp`.
    """

    name = "serp"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "SERP",
        "description": "Template for spiders that extract search engine results.",
    }

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> scrapy.Spider:
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider._init_input()
        return spider

    def _init_input(self):
        urls_file = self.args.urls_file
        if urls_file:
            response = requests.get(urls_file)
            urls = load_url_list(response.text)
            self.logger.info(f"Loaded {len(urls)} initial URLs from {urls_file}.")
            self.start_urls = urls
        elif self.args.urls:
            self.start_urls = self.args.urls
        else:
            self.start_urls = [self.args.url]
        self.allowed_domains = list(set(get_domain(url) for url in self.start_urls))

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
