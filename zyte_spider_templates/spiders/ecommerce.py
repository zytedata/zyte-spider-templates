from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Optional, Union, cast

import scrapy
from pydantic import BaseModel, ConfigDict, Field
from scrapy.crawler import Crawler
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import Args
from zyte_common_items import (
    CustomAttributes,
    ProbabilityRequest,
    Product,
    ProductNavigation,
)

from zyte_spider_templates.heuristics import is_homepage
from zyte_spider_templates.params import parse_input_params
from zyte_spider_templates.spiders.base import (
    ARG_SETTING_PRIORITY,
    INPUT_GROUP,
    BaseSpider,
)
from zyte_spider_templates.utils import get_domain

from ..documentation import document_enum
from ..params import (
    CustomAttrsInputParam,
    CustomAttrsMethodParam,
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    UrlParam,
    UrlsFileParam,
    UrlsParam,
)

if TYPE_CHECKING:
    # typing.Self requires Python 3.11
    from typing_extensions import Self


@document_enum
class EcommerceCrawlStrategy(str, Enum):
    automatic: str = "automatic"
    """
    Automatically select the best approach. A good default for most use cases.
    Currently it uses heuristics only on the homepages of websites (similar to
    Full strategy), and follows product, category and pagination links on other
    pages (similar to Navigation strategy).
    """

    full: str = "full"
    """
    Follow most links on the website to discover and extract as many products
    as possible. If an input URL is a link to a particular category on a
    website, the spider may crawl products outside this category. Try this
    strategy if other strategies miss items.
    """

    navigation: str = "navigation"
    """
    Follow pagination, subcategories, and product links only. If an input URL
    is a link to a particular category on a website, the spider will try to
    stay within this category.
    """

    pagination_only: str = "pagination_only"
    """
    Follow pagination and product links only. This strategy is similar to
    Navigation, but it doesn't support subcategories. Use it when you need the
    spider to stay within a certain category on a website, but Automatic or
    Navigation strategies fail to do so because of misclassified subcategory links.
    """

    direct_item: str = "direct_item"
    """
    Directly extract products from the provided URLs, without any crawling. To
    use this strategy, pass individual product URLs to the spider, not the
    website or product category URLs. Common use cases are product monitoring
    and batch extraction.
    """


class EcommerceCrawlStrategyParam(BaseModel):
    crawl_strategy: EcommerceCrawlStrategy = Field(
        title="Crawl strategy",
        description="Determines how the start URL and follow-up URLs are crawled.",
        default=EcommerceCrawlStrategy.automatic,
        json_schema_extra={
            "enumMeta": {
                EcommerceCrawlStrategy.automatic: {
                    "description": (
                        "Automatically select the best approach. A good "
                        "default for most use cases. Currently it uses "
                        "heuristics only on the homepages of websites (similar "
                        "to Full strategy), and follows product, category and "
                        "pagination links on other pages (similar to Navigation "
                        "strategy)."
                    ),
                    "title": "Automatic",
                },
                EcommerceCrawlStrategy.full: {
                    "title": "Full",
                    "description": (
                        "Follow most links on the website to discover and "
                        "extract as many products as possible. If an input URL "
                        "is a link to a particular category on a website, the "
                        "spider may crawl products outside this category. Try "
                        "this strategy if other strategies miss items."
                    ),
                },
                EcommerceCrawlStrategy.navigation: {
                    "title": "Navigation",
                    "description": (
                        "Follow pagination, subcategories, and product links "
                        "only. If an input URL is a link to a particular "
                        "category on a website, the spider will try to stay "
                        "within this category."
                    ),
                },
                EcommerceCrawlStrategy.pagination_only: {
                    "title": "Pagination Only",
                    "description": (
                        "Follow pagination and product links only. This "
                        "strategy is similar to Navigation, but it doesn't "
                        "support subcategories. Use it when you need the "
                        "spider to stay within a certain category on a "
                        "website, but Automatic or Navigation strategies fail "
                        "to do so because of misclassified subcategory links."
                    ),
                },
                EcommerceCrawlStrategy.direct_item: {
                    "title": "Direct URLs to Product",
                    "description": (
                        "Directly extract products from the provided URLs, "
                        "without any crawling. To use this strategy, pass "
                        "individual product URLs to the spider, not the "
                        "website or product category URLs. Common use cases "
                        "are product monitoring and batch extraction."
                    ),
                },
            },
        },
    )


class EcommerceSpiderParams(
    CustomAttrsMethodParam,
    CustomAttrsInputParam,
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    EcommerceCrawlStrategyParam,
    UrlsFileParam,
    UrlsParam,
    UrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        json_schema_extra={
            "groups": [
                INPUT_GROUP,
            ],
        },
    )


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
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> Self:
        spider = super(EcommerceSpider, cls).from_crawler(crawler, *args, **kwargs)
        parse_input_params(spider)
        spider._init_extract_from()
        return spider

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
            if self.args.crawl_strategy == EcommerceCrawlStrategy.direct_item
            else self.parse_navigation
        )
        meta: Dict[str, Any] = {
            "crawling_logs": {
                "page_type": "product"
                if self.args.crawl_strategy == EcommerceCrawlStrategy.direct_item
                else "productNavigation"
            },
        }
        if (
            self.args.crawl_strategy == EcommerceCrawlStrategy.direct_item
            and self._custom_attrs_dep
        ):
            meta["inject"] = [
                self._custom_attrs_dep,
            ]

        if self.args.crawl_strategy == EcommerceCrawlStrategy.full:
            meta["page_params"] = {"full_domain": get_domain(url)}
        elif self.args.crawl_strategy == EcommerceCrawlStrategy.automatic:
            if is_homepage(url):
                meta["page_params"] = {"full_domain": get_domain(url)}
                self.logger.info(
                    f"[Automatic Strategy] The input URL {url} seems to be a homepage. "
                    f"Heuristics will be used on it to crawl other pages which might have products."
                )
            else:
                self.logger.info(
                    f"[Automatic Strategy] The input URL {url} doesn't seem to be a homepage. "
                    f"Heuristics won't be used to crawl other pages which might have products."
                )

        return scrapy.Request(
            url=url,
            callback=callback,
            meta=meta,
        )

    def start_requests(self) -> Iterable[scrapy.Request]:
        for url in self.start_urls:
            yield self.get_start_request(url)

    def parse_navigation(
        self, response: DummyResponse, navigation: ProductNavigation
    ) -> Iterable[scrapy.Request]:
        page_params = self._modify_page_params_for_heuristics(
            response.meta.get("page_params")
        )

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
                yield self.get_nextpage_request(
                    cast(ProbabilityRequest, navigation.nextPage)
                )

        if self.args.crawl_strategy != EcommerceCrawlStrategy.pagination_only:
            for request in navigation.subCategories or []:
                yield self.get_subcategory_request(request, page_params=page_params)

    def parse_product(
        self, response: DummyResponse, product: Product, dynamic: DynamicDeps
    ) -> Iterable[
        Union[Product, Dict[str, Union[Product, Optional[CustomAttributes]]]]
    ]:
        probability = product.get_probability()

        # TODO: convert to a configurable parameter later on after the launch
        if probability is None or probability >= 0.1:
            if self.args.custom_attrs_input:
                yield {
                    "product": product,
                    "customAttributes": dynamic.get(CustomAttributes),
                }
            else:
                yield product
        else:
            assert self.crawler.stats
            self.crawler.stats.inc_value("drop_item/product/low_probability")
            self.logger.info(
                f"Ignoring item from {response.url} since its probability is "
                f"less than threshold of 0.1:\n{product}"
            )

    @staticmethod
    def get_parse_navigation_request_priority(request: ProbabilityRequest) -> int:
        if (
            not hasattr(request, "metadata")
            or not request.metadata
            or request.metadata.probability is None
        ):
            return 0
        return int(100 * request.metadata.probability)

    def get_parse_navigation_request(
        self,
        request: ProbabilityRequest,
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
        request: ProbabilityRequest,
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
        request: ProbabilityRequest,
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
        meta: Dict[str, Any] = {
            "crawling_logs": {
                "name": request.name,
                "probability": probability,
                "page_type": "product",
            },
        }
        if self._custom_attrs_dep:
            meta["inject"] = [
                self._custom_attrs_dep,
            ]

        scrapy_request = request.to_scrapy(
            callback=callback,
            priority=priority,
            meta=meta,
        )
        scrapy_request.meta["allow_offsite"] = True
        return scrapy_request

    def _modify_page_params_for_heuristics(
        self, page_params: Optional[Dict]
    ) -> Dict[str, Any]:
        page_params = page_params or {}
        # Only allow heuristic extraction of links in non-homepage when on "full" crawl.
        if self.args.crawl_strategy != EcommerceCrawlStrategy.full:
            page_params.pop("full_domain", None)

        return page_params
