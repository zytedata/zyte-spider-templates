from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional

import attrs
import requests
import scrapy
from pydantic import BaseModel, ConfigDict, Field
from scrapy.crawler import Crawler
from scrapy.exceptions import CloseSpider
from scrapy.settings import BaseSettings
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import Args
from web_poet import BrowserResponse, HttpResponse
from zyte_common_items import (
    Article,
    ArticleNavigation,
    ProbabilityMetadata,
    ProbabilityRequest,
)
from zyte_common_items.pipelines import DropLowProbabilityItemPipeline

from zyte_spider_templates.documentation import document_enum
from zyte_spider_templates.pages.article_heuristics import is_feed_request
from zyte_spider_templates.params import (
    INPUT_GROUP,
    ExtractFrom,
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    MaxRequestsPerSeedParam,
    UrlParam,
    UrlsFileParam,
    UrlsParam,
)
from zyte_spider_templates.spiders.base import ARG_SETTING_PRIORITY, BaseSpider

from ..utils import load_url_list

if TYPE_CHECKING:
    # typing.Self requires Python 3.11
    from typing_extensions import Self


@attrs.define
class RequestTypeItemEnum:
    name: str = attrs.field(default="no_name")
    priority: int = attrs.field(default=0)
    page_type: str = attrs.field(default="no_page_type")
    inject: list = attrs.field(default=[])


class RequestType(Enum):
    SEED: RequestTypeItemEnum = RequestTypeItemEnum(
        name="seed",
        priority=40,
        page_type="articleNavigation",
        inject=[ArticleNavigation],
    )
    ARTICLE: RequestTypeItemEnum = RequestTypeItemEnum(
        name="article", priority=30, page_type="article", inject=[Article]
    )
    ARTICLE_AND_NAVIGATION: RequestTypeItemEnum = RequestTypeItemEnum(
        name="article_and_navigation",
        priority=20,
        page_type="articleNavigation-heuristics",
        inject=[Article, ArticleNavigation],
    )
    NAVIGATION: RequestTypeItemEnum = RequestTypeItemEnum(
        name="navigation",
        priority=10,
        page_type="subCategories",
        inject=[ArticleNavigation],
    )
    NEXT_PAGE: RequestTypeItemEnum = RequestTypeItemEnum(
        name="nextPage", priority=100, page_type="nextPage", inject=[ArticleNavigation]
    )


class IncrementalParam(BaseModel):
    incremental: bool = Field(
        description=(
            "Skip items with URLs already stored in the specified Zyte Scrapy Cloud Collection. "
            "This feature helps avoid reprocessing previously crawled items and requests by comparing "
            "their URLs against the stored collection."
        ),
        default=False,
    )
    incremental_collection_name: Optional[str] = Field(
        description=(
            "Name of the Zyte Scrapy Cloud Collection used during an incremental crawl."
            "By default, a Collection named after the spider (or virtual spider) is used, "
            "meaning that matching URLs from previous runs of the same spider are skipped, "
            "provided those previous runs had `incremental` argument set to `true`."
            "Using a different collection name makes sense, for example, in the following cases:"
            "- different spiders share a collection."
            "- the same spider uses different collections (e.g., for development runs vs. production runs). "
            "Only ASCII alphanumeric characters and underscores are allowed in the collection name."
        ),
        default=None,
        pattern="^[a-zA-Z0-9_]+$",
    )


@document_enum
class ArticleCrawlStrategy(str, Enum):
    full: str = "full"
    """Follow most links within each domain from the list of URLs in an
    attempt to discover and extract as many articles as possible."""

    direct_item: str = "direct_item"
    """Treat input URLs as direct links to articles, and extract an
    article from each."""


class ArticleCrawlStrategyParam(BaseModel):
    crawl_strategy: ArticleCrawlStrategy = Field(
        title="Crawl Strategy",
        description="Determines how input URLs and follow-up URLs are crawled.",
        default=ArticleCrawlStrategy.full,
        json_schema_extra={
            "enumMeta": {
                ArticleCrawlStrategy.full: {
                    "title": "Full",
                    "description": (
                        "Follow most links within each domain from the list of URLs in an "
                        "attempt to discover and extract as many articles as possible."
                    ),
                },
                ArticleCrawlStrategy.direct_item: {
                    "title": "Direct URLs to Articles",
                    "description": (
                        "Treat input URLs as direct links to articles, and "
                        "extract an article from each."
                    ),
                },
            },
        },
    )


class ArticleSpiderParams(
    ExtractFromParam,
    MaxRequestsPerSeedParam,
    MaxRequestsParam,
    GeolocationParam,
    ArticleCrawlStrategyParam,
    IncrementalParam,
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


class ArticleSpider(Args[ArticleSpiderParams], BaseSpider):
    """Yield articles from one or more websites that contain articles.

    See :class:`~zyte_spider_templates.spiders.article.ArticleSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`article`.
    """

    name: str = "article"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "Article",
        "description": "[Experimental] Template for spiders that extract article data from news or blog websites.",
    }

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> Self:
        spider = super(ArticleSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider._init_input()
        spider._init_extract_from()
        spider._init_incremental()

        if spider.args.max_requests_per_seed:
            spider.settings.set(
                "MAX_REQUESTS_PER_SEED",
                spider.args.max_requests_per_seed,
                priority=ARG_SETTING_PRIORITY,
            )

        return spider

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        settings["ITEM_PIPELINES"][DropLowProbabilityItemPipeline] = 0

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

    def _init_extract_from(self):
        if self.args.extract_from is not None:
            self.settings.set(
                "ZYTE_API_PROVIDER_PARAMS",
                {
                    "articleOptions": {"extractFrom": self.args.extract_from},
                    "articleNavigationOptions": {"extractFrom": self.args.extract_from},
                    **self.settings.get("ZYTE_API_PROVIDER_PARAMS", {}),
                },
                priority=ARG_SETTING_PRIORITY,
            )

    def _init_incremental(self):
        self.settings.set(
            "INCREMENTAL_CRAWL_ENABLED",
            self.args.incremental,
            priority=ARG_SETTING_PRIORITY,
        )
        if self.args.incremental:
            self.settings.set(
                "NAVIGATION_DEPTH_LIMIT",
                1,
                priority=ARG_SETTING_PRIORITY,
            )
            self.logger.info(
                "NAVIGATION_DEPTH_LIMIT=1 is set because the incremental crawling is enabled."
            )
            if self.args.incremental_collection_name:
                self.settings.set(
                    "INCREMENTAL_CRAWL_COLLECTION_NAME",
                    self.args.incremental_collection_name,
                    priority=ARG_SETTING_PRIORITY,
                )
                self.logger.info(
                    f"INCREMENTAL_CRAWL_COLLECTION_NAME={self.args.incremental_collection_name} "
                )

    def _update_inject_meta(self, meta: Dict[str, Any], is_feed: bool) -> None:
        """
        The issue: `HeuristicsArticleNavigationPage` has only `AnyResponse` as a dependency, so
        the current implementation of `ScrapyZyteApiProvider` always uses `HttpResponse`
        to produce the ArticleNavigation item, regardless of the `extract_from` argument.

        This function forces `browserHtml` extraction when `extract_from=browserHtml`
        for Article and ArticleNavigation pages, while continuing to use
        `HttpResponse` for feeds.
        """

        if is_feed:
            inject = meta["inject"].copy()
            inject.append(HttpResponse)
            meta["inject"] = inject
            return None

        if self.args.extract_from == ExtractFrom.browserHtml:
            inject = meta["inject"].copy()
            inject.append(BrowserResponse)
            meta["inject"] = inject
        return None

    def _update_request_name(self, req: ProbabilityRequest) -> None:
        replacements = {
            "[heuristics][articleNavigation][article]": "[article or subCategories]",
            "[heuristics][articleNavigation][feed items]": "[feed items or subCategories]",
        }
        for old_name, new_name in replacements.items():
            req.name = (req.name or "").replace(old_name, new_name)

    def start_requests(self) -> Iterable[scrapy.Request]:
        if self.args.crawl_strategy == ArticleCrawlStrategy.full:
            request_type = RequestType.SEED
            probability = None
        elif self.args.crawl_strategy == ArticleCrawlStrategy.direct_item:
            request_type = RequestType.ARTICLE
            probability = 1.0
        else:
            self.logger.error(
                f"The strategy `{self.args.crawl_strategy}` is not supported. "
                f"Currently, only these strategies are supported: `full` and `direct_item`."
            )
            raise CloseSpider("not_supported_strategy_type")

        for url in self.start_urls:
            meta = {"request_type": request_type}
            with self._log_request_exception:
                yield self.get_parse_request(
                    ProbabilityRequest(
                        url=url,
                        name=f"[{request_type.value.name}]",
                        metadata=ProbabilityMetadata(probability=probability),
                    ),
                    meta=meta,
                    is_feed=False,
                )

    def parse_dynamic(
        self,
        response: DummyResponse,
        dynamic: DynamicDeps,
    ) -> Iterable[scrapy.Request]:
        if Article in dynamic:
            yield from self._parse_as_article(response, dynamic)

        if ArticleNavigation in dynamic:
            yield from self._parse_as_navigation(response, dynamic)

    def _parse_as_article(
        self, response: DummyResponse, dynamic: DynamicDeps
    ) -> Iterable[scrapy.Request]:
        yield dynamic[Article]

    def _parse_as_navigation(
        self, response: DummyResponse, dynamic: DynamicDeps
    ) -> Iterable[scrapy.Request]:
        navigation = dynamic[ArticleNavigation]

        # Handle the nextPage link if it exists
        if navigation.nextPage:
            if not navigation.items:
                self.logger.info(
                    f"Ignoring nextPage link {navigation.nextPage} since there "
                    f"are no article links found in {navigation.url}"
                )
            else:
                meta = {
                    "request_type": RequestType.NEXT_PAGE,
                    "increase_navigation_depth": False,
                }
                with self._log_request_exception:
                    yield self.get_parse_request(
                        navigation.nextPage, meta=meta, is_feed=False
                    )

        subcategories = navigation.subCategories or []
        items = navigation.items or []
        subcategories_urls = {req.url for req in subcategories}
        items_urls = {req.url for req in items}

        # Preprocess the list of requests for final_navigation_page
        if response.meta.get("final_navigation_page"):
            self.logger.debug(
                f"Navigation links from {response.url} response are not followed, because"
                f"{response.meta.get('navigation_depth')} max navigation_depth has been reached."
            )
            self.crawler.stats.inc_value("navigation_depth/final_navigation_page")  # type: ignore[union-attr]
            subcategories_urls -= items_urls

        # Iterate over both subcategories and items
        for req in items + subcategories:
            # Determine request type and meta information
            # `increase_navigation_depth` and `is_feed` flags are clearly defined for each request type
            if req.url in subcategories_urls:
                if req.url not in items_urls:
                    # Subcategory request only
                    is_feed = is_feed_request(req)
                    increase_navigation_depth = not is_feed
                    request_type = RequestType.NAVIGATION
                else:
                    # Request for both subcategory and item
                    self._update_request_name(req)
                    is_feed = False
                    increase_navigation_depth = True
                    request_type = RequestType.ARTICLE_AND_NAVIGATION
            else:
                # Article request only
                is_feed = False
                increase_navigation_depth = False
                request_type = RequestType.ARTICLE

            meta = {
                "request_type": request_type,
                # processed here to be able to customize this value for each request type
                "increase_navigation_depth": increase_navigation_depth,
            }

            with self._log_request_exception:
                yield self.get_parse_request(req, meta=meta, is_feed=is_feed)

    def get_parse_request(
        self,
        request: ProbabilityRequest,
        meta: Optional[Dict[Any, Any]] = None,
        is_feed: bool = False,
        **kwargs,
    ) -> scrapy.Request:
        meta = meta or {}
        request_type = meta["request_type"].value
        meta.update(
            {
                "crawling_logs": {
                    "name": request.name,
                    "page_type": request_type.page_type,
                    "probability": request.get_probability(),
                },
                "inject": request_type.inject,
            },
        )
        self._update_inject_meta(meta, is_feed)

        return request.to_scrapy(
            callback=self.parse_dynamic,
            errback=self.errback_navigation,
            priority=request_type.priority,
            meta=meta,
            **kwargs,
        )

    def errback_navigation(self, failure) -> None:
        """Request error"""
        comm_msg = "article_spider/request_error"
        deps = failure.request.meta["inject"]
        deps_msg = "-".join([d.__name__[0].lower() + d.__name__[1:] for d in deps])
        assert self.crawler.stats
        self.crawler.stats.inc_value(f"{comm_msg}/{deps_msg}")
