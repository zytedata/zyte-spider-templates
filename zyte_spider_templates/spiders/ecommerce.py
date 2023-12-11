from enum import Enum
from typing import Any, Dict, Iterable, Optional

import scrapy
from pydantic import Field
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy_poet import DummyResponse
from scrapy_spider_metadata import Args
from zyte_common_items import Product, ProductNavigation

from zyte_spider_templates.documentation import document_enum
from zyte_spider_templates.spiders.base import BaseSpider, BaseSpiderParams


@document_enum
class EcommerceCrawlStrategy(str, Enum):
    full: str = "full"
    """Follow most links within the domain of URL in an attempt to discover and
    extract as many products as possible."""

    navigation: str = "navigation"
    """Follow pagination, subcategories, and product detail pages."""

    pagination_only: str = "pagination_only"
    """Follow pagination and product detail pages. SubCategory links are
    ignored. Use this when some subCategory links are misidentified by
    ML-extraction."""


@document_enum
class ExtractFrom(str, Enum):
    httpResponseBody: str = "httpResponseBody"
    """Use HTTP responses. Cost-efficient and fast extraction method, which
    works well on many websites."""

    browserHtml: str = "browserHtml"
    """Use browser rendering. Often provides the best quality."""


class EcommerceSpiderParams(BaseSpiderParams):
    crawl_strategy: EcommerceCrawlStrategy = Field(
        title="Crawl strategy",
        description="Determines how the start URL and follow-up URLs are crawled.",
        default=EcommerceCrawlStrategy.navigation,
        json_schema_extra={
            "enumMeta": {
                EcommerceCrawlStrategy.full: {
                    "title": "Full",
                    "description": "Follow most links within the domain of URL in an attempt to discover and extract as many products as possible.",
                },
                EcommerceCrawlStrategy.navigation: {
                    "title": "Navigation",
                    "description": "Follow pagination, subcategories, and product detail pages.",
                },
                EcommerceCrawlStrategy.pagination_only: {
                    "title": "Pagination Only",
                    "description": (
                        "Follow pagination and product detail pages. SubCategory links are ignored. "
                        "Use this when some subCategory links are misidentified by ML-extraction."
                    ),
                },
            },
        },
    )
    extract_from: Optional[ExtractFrom] = Field(
        title="Extraction source",
        description=(
            "Whether to perform extraction using a browser request "
            "(browserHtml) or an HTTP request (httpResponseBody)."
        ),
        default=None,
        json_schema_extra={
            "enumMeta": {
                ExtractFrom.browserHtml: {
                    "title": "browserHtml",
                    "description": "Use browser rendering. Often provides the best quality.",
                },
                ExtractFrom.httpResponseBody: {
                    "title": "httpResponseBody",
                    "description": "Use HTTP responses. Cost-efficient and fast extraction method, which works well on many websites.",
                },
            },
        },
    )


class EcommerceSpider(Args[EcommerceSpiderParams], BaseSpider):
    """Yield products from an e-commerce website.

    *url* is the start URL, e.g. a homepage or category page.

    *crawl_strategy* determines how the start URL and follow-up URLs are
    crawled:

    -   ``"navigation"`` (default): follow pagination, subcategories, and
        product detail pages.

    -   ``"full"``: follow most links within the domain of *url* in an attempt to
        discover and extract as many products as it can.

    *geolocation* (optional) is an ISO 3166-1 alpha-2 2-character string specified in:
    https://docs.zyte.com/zyte-api/usage/reference.html#operation/extract/request/geolocation

    *max_requests* (optional) specifies the max number of Zyte API requests
    allowed for the crawl.

    *extract_from* (optional) allows to enforce extracting the data from
    either "browserHtml" or "httpResponseBody".
    """

    name = "ecommerce"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "E-commerce",
        "description": "Template for spiders that extract product data from e-commerce websites.",
    }

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> scrapy.Spider:
        spider = super(EcommerceSpider, cls).from_crawler(crawler, *args, **kwargs)

        if spider.args.extract_from is not None:
            spider.settings.set(
                "ZYTE_API_PROVIDER_PARAMS",
                {
                    "productOptions": {"extractFrom": spider.args.extract_from},
                    "productNavigationOptions": {
                        "extractFrom": spider.args.extract_from
                    },
                },
            )

        return spider

    def start_requests(self) -> Iterable[Request]:
        page_params = {}
        if self.args.crawl_strategy == EcommerceCrawlStrategy.full:
            page_params = {"full_domain": self.allowed_domains[0]}

        yield Request(
            url=self.args.url,
            callback=self.parse_navigation,
            meta={
                "page_params": page_params,
                "crawling_logs": {"page_type": "productNavigation"},
            },
        )

    def parse_navigation(
        self, response: DummyResponse, navigation: ProductNavigation
    ) -> Iterable[Request]:
        page_params = response.meta.get("page_params")

        for request in navigation.items or []:
            yield self.get_parse_product_request(request)
        if navigation.nextPage:
            yield self.get_nextpage_request(navigation.nextPage)

        if self.args.crawl_strategy != EcommerceCrawlStrategy.pagination_only:
            for request in navigation.subCategories or []:
                yield self.get_subcategory_request(request, page_params=page_params)

    def parse_product(
        self, response: DummyResponse, product: Product
    ) -> Iterable[Product]:
        probability = product.get_probability()

        # TODO: convert to a configurable parameter later on after the launch
        if probability is None or probability >= 0.1:
            yield product
        else:
            self.logger.info(
                f"Ignoring item from {response.url} since its probability is "
                f"less than threshold of 0.1:\n{product}"
            )
