from enum import Enum
from typing import Any, Callable, Dict, Iterable, Optional, Union

import requests
import scrapy
from pydantic import BaseModel, Field
from scrapy import Request
from scrapy.crawler import Crawler
from scrapy_poet import DummyResponse
from scrapy_spider_metadata import Args
from zyte_common_items import ProbabilityRequest, Product, ProductNavigation

from zyte_spider_templates.spiders.base import (
    ARG_SETTING_PRIORITY,
    BaseSpider,
    BaseSpiderParams,
)
from zyte_spider_templates.utils import get_domain

from ..documentation import document_enum
from ..utils import load_url_list


@document_enum
class EcommerceCrawlStrategy(str, Enum):
    full: str = "full"
    """Follow most links within the domain of URL in an attempt to discover and
    extract as many products as possible."""

    navigation: str = "navigation"
    """Follow pagination, subcategories, and product detail pages.

    Pagination Only is a better choice if the target URL does not have
    subcategories, or if Zyte API is misidentifying some URLs as subcategories.
    """

    pagination_only: str = "pagination_only"
    """Follow pagination and product detail pages. Subcategory links are
    ignored."""

    direct_product: str = "direct_product"
    """Treat input URLs as direct links to product detail pages, and
    extract a product from each."""


class EcommerceCrawlStrategyParam(BaseModel):
    crawl_strategy: EcommerceCrawlStrategy = Field(
        title="Crawl strategy",
        description="Determines how the start URL and follow-up URLs are crawled.",
        default=EcommerceCrawlStrategy.full,
        json_schema_extra={
            "enumMeta": {
                EcommerceCrawlStrategy.full: {
                    "title": "Full",
                    "description": "Follow most links within the domain of URL in an attempt to discover and extract as many products as possible.",
                },
                EcommerceCrawlStrategy.navigation: {
                    "title": "Navigation",
                    "description": (
                        "Follow pagination, subcategories, and product detail "
                        "pages. Pagination Only is a better choice if the "
                        "target URL does not have subcategories, or if Zyte "
                        "API is misidentifying some URLs as subcategories."
                    ),
                },
                EcommerceCrawlStrategy.pagination_only: {
                    "title": "Pagination Only",
                    "description": (
                        "Follow pagination and product detail pages. Subcategory links are ignored."
                    ),
                },
                EcommerceCrawlStrategy.direct_product: {
                    "title": "Direct URLs to Product",
                    "description": (
                        "Treat input URLs as direct links to product detail pages, and "
                        "extract a product from each."
                    ),
                },
            },
        },
    )


class EcommerceSpiderParams(EcommerceCrawlStrategyParam, BaseSpiderParams):
    pass


class EcommerceSpider(Args[EcommerceSpiderParams], BaseSpider):
    """Yield products from an e-commerce website.

    See :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`e-commerce`.
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
        spider._init_input()
        spider._init_extract_from()
        return spider

    def _init_input(self):
        urls_file = self.args.urls_file
        if urls_file:
            response = requests.get(urls_file)
            urls = load_url_list(response.text)
            self.logger.info(f"Loaded {len(urls)} initial URLs from {urls_file}.")
            self.start_urls = urls
        else:
            self.start_urls = [self.args.url]
        self.allowed_domains = list(set(get_domain(url) for url in self.start_urls))

    def _init_extract_from(self):
        if self.args.extract_from is not None:
            self.settings.set(
                "ZYTE_API_PROVIDER_PARAMS",
                {
                    "productOptions": {"extractFrom": self.args.extract_from},
                    "productNavigationOptions": {"extractFrom": self.args.extract_from},
                    **self.settings.get("ZYTE_API_PROVIDER_PARAMS", {}),
                },
                priority=ARG_SETTING_PRIORITY,
            )

    def get_start_request(self, url):
        callback = (
            self.parse_product
            if self.args.crawl_strategy == EcommerceCrawlStrategy.direct_product
            else self.parse_navigation
        )
        meta = {
            "crawling_logs": {"page_type": "productNavigation"},
        }
        if self.args.crawl_strategy == EcommerceCrawlStrategy.full:
            meta["page_params"] = {"full_domain": get_domain(url)}
        return Request(
            url=url,
            callback=callback,
            meta=meta,
        )

    def start_requests(self) -> Iterable[Request]:
        for url in self.start_urls:
            yield self.get_start_request(url)

    def parse_navigation(
        self, response: DummyResponse, navigation: ProductNavigation
    ) -> Iterable[Request]:
        page_params = response.meta.get("page_params")

        products = navigation.items or []
        for request in products:
            yield self.get_parse_product_request(request)

        if navigation.nextPage:
            if not products:
                self.logger.info(
                    f"Ignoring nextPage link {navigation.nextPage} since there "
                    f"are no product links found in {navigation.url}"
                )
            else:
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
            self.crawler.stats.inc_value("drop_item/product/low_probability")
            self.logger.info(
                f"Ignoring item from {response.url} since its probability is "
                f"less than threshold of 0.1:\n{product}"
            )

    @staticmethod
    def get_parse_navigation_request_priority(
        request: Union[ProbabilityRequest, Request]
    ) -> int:
        if (
            not hasattr(request, "metadata")
            or not request.metadata
            or request.metadata.probability is None
        ):
            return 0
        return int(100 * request.metadata.probability)

    def get_parse_navigation_request(
        self,
        request: Union[ProbabilityRequest, Request],
        callback: Optional[Callable] = None,
        page_params: Optional[Dict[str, Any]] = None,
        priority: Optional[int] = None,
        page_type: str = "productNavigation",
    ) -> scrapy.Request:
        callback = callback or self.parse_navigation

        return request.to_scrapy(
            callback=callback,
            priority=priority or self.get_parse_navigation_request_priority(request),
            meta={
                "page_params": page_params or {},
                "crawling_logs": {
                    "name": request.name or "",
                    "probability": request.get_probability(),
                    "page_type": page_type,
                },
            },
        )

    def get_subcategory_request(
        self,
        request: Union[ProbabilityRequest, Request],
        callback: Optional[Callable] = None,
        page_params: Optional[Dict[str, Any]] = None,
        priority: Optional[int] = None,
    ) -> scrapy.Request:
        page_type = "subCategories"
        request_name = request.name or ""
        if "[heuristics]" not in request_name:
            page_params = None
        else:
            page_type = "productNavigation-heuristics"
            request.name = request_name.replace("[heuristics]", "").strip()
        return self.get_parse_navigation_request(
            request,
            callback,
            page_params,
            priority,
            page_type,
        )

    def get_nextpage_request(
        self,
        request: Union[ProbabilityRequest, Request],
        callback: Optional[Callable] = None,
        page_params: Optional[Dict[str, Any]] = None,
    ):
        return self.get_parse_navigation_request(
            request, callback, page_params, self._NEXT_PAGE_PRIORITY, "nextPage"
        )

    def get_parse_product_request_priority(self, request: ProbabilityRequest) -> int:
        probability = request.get_probability() or 0
        return int(100 * probability) + self._NEXT_PAGE_PRIORITY

    def get_parse_product_request(
        self, request: ProbabilityRequest, callback: Optional[Callable] = None
    ) -> scrapy.Request:
        callback = callback or self.parse_product
        priority = self.get_parse_product_request_priority(request)

        probability = request.get_probability()

        scrapy_request = request.to_scrapy(
            callback=callback,
            priority=priority,
            meta={
                "crawling_logs": {
                    "name": request.name,
                    "probability": probability,
                    "page_type": "product",
                }
            },
        )
        scrapy_request.meta["allow_offsite"] = True
        return scrapy_request
