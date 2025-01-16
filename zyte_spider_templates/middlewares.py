import json
import logging
import warnings
from collections import defaultdict
from datetime import datetime
from typing import (
    Any,
    AsyncIterable,
    Dict,
    Generator,
    Iterable,
    List,
    Optional,
    Set,
    Union,
)
from warnings import warn

from scrapy import Request, Spider
from scrapy.crawler import Crawler
from scrapy.dupefilters import RFPDupeFilter
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.http import Response
from scrapy.utils.httpobj import urlparse_cached
from scrapy.utils.url import url_is_from_any_domain
from scrapy_poet import DynamicDeps
from zyte_common_items import Article, ArticleNavigation, Item

try:
    from scrapy.downloadermiddlewares.offsite import OffsiteMiddleware
except ImportError:
    from scrapy.spidermiddlewares.offsite import OffsiteMiddleware  # type: ignore[assignment]

from zyte_spider_templates.utils import get_domain

logger = logging.getLogger(__name__)


warnings.filterwarnings("ignore", message="model will result in indexing errors*")


class CrawlingLogsMiddleware:
    """For each page visited, this logs what the spider has extracted and planning
    to crawl next.
    The motivation for such logs is to easily debug the crawling behavior and see
    what went wrong. Apart from high-level summarized information, this also includes
    JSON-formatted data so that it can easily be parsed later on.

    Some notes:
        - ``scrapy.utils.request.request_fingerprint`` is used to match what
          https://github.com/scrapinghub/scrapinghub-entrypoint-scrapy uses.
          This makes it easier to work with since we can easily match it with
          the fingerprints logged in Scrapy Cloud's request data.
    """

    unknown_page_type = "unknown"

    @classmethod
    def from_crawler(cls, crawler):
        try:
            result = cls(crawler)
        except TypeError:
            warn(
                (
                    "Subclasses of CrawlingLogsMiddleware must now accept a "
                    "crawler parameter in their __init__ method. This will "
                    "become an error in the future."
                ),
                DeprecationWarning,
            )
            result = cls()
            result._crawler = crawler
        return result

    def __init__(self, crawler=None):
        self._crawler = crawler

    def _fingerprint(self, request):
        return self._crawler.request_fingerprinter.fingerprint(request).hex()

    def process_spider_output(self, response, result, spider):
        result = list(result)
        crawl_logs = self.crawl_logs(response, result)
        logger.info(crawl_logs)
        return result

    def crawl_logs(self, response, result):
        current_page_type = response.meta.get("crawling_logs", {}).get("page_type")
        fingerprint = self._fingerprint(response.request)
        data: Dict[str, Any] = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current": {
                "url": response.url,
                "request_url": response.request.url,
                # TODO: update this when the following is updated to use the same fingerprinter
                # with Scrapy: https://github.com/scrapinghub/scrapinghub-entrypoint-scrapy/
                "request_fingerprint": fingerprint,
                "page_type": current_page_type,
                "probability": response.meta.get("crawling_logs", {}).get(
                    "probability"
                ),
            },
            "to_crawl": defaultdict(list),
        }

        if result:
            for entry in result:
                if not isinstance(entry, Request):
                    continue

                crawling_logs = entry.meta.get("crawling_logs", {})
                entry_fingerprint = self._fingerprint(entry)
                crawling_logs.update(
                    {
                        "request_url": entry.url,
                        "request_priority": entry.priority,
                        "request_fingerprint": entry_fingerprint,
                    }
                )

                page_type = crawling_logs.get("page_type")
                if not page_type:
                    page_type = self.unknown_page_type

                data["to_crawl"][page_type].append(crawling_logs)

        if data["to_crawl"]:
            summary = ["Number of Requests per page type:"]
            for page_type, requests in data["to_crawl"].items():
                summary.append(f"- {page_type}: {len(requests)}")
        else:
            summary = ["Nothing to crawl."]

        report = [
            f"Crawling Logs for {response.url} (parsed as: {current_page_type}):",
            "\n".join(summary),
            "Structured Logs:",
            json.dumps(data, indent=2),
        ]
        return "\n".join(report)


class AllowOffsiteMiddleware(OffsiteMiddleware):
    def should_follow(self, request: Request, spider: Spider) -> bool:
        if "zyte_api" in request.meta:
            # The request looks like a dependency injection request, and any
            # domain-based filtering should have been handled in the original
            # request handling, before dependency injection.
            return True
        if request.meta.get("allow_offsite") is True:
            return True
        return super().should_follow(request, spider)


class MaxRequestsPerSeedDownloaderMiddleware:
    """This middleware limits the number of requests that each seed request can subsequently
    have.

    To enable this middleware, set the ``MAX_REQUESTS_PER_SEED`` setting to
    the desired positive value. Non-positive integers (i.e. 0 and below)
    imposes no limit and disables this middleware.

    By default, all start requests are considered seed requests, and all other
    requests are not.

    Please note that you also need to enable TrackSeedsSpiderMiddleware to make this work.
    """

    def __init__(self, crawler: Crawler):
        assert crawler.spider
        max_requests_per_seed = max(
            0, crawler.spider.settings.getint("MAX_REQUESTS_PER_SEED", 0)
        )
        if not max_requests_per_seed:
            raise NotConfigured
        self.crawler = crawler
        self.requests_per_seed: defaultdict = defaultdict(int)
        self.seeds_reached_limit: Set[str] = set()
        self.max_requests_per_seed = max_requests_per_seed

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        seed = request.meta.get("seed")
        if seed is None:
            return
        if self.max_requests_per_seed_reached(seed):
            self.seeds_reached_limit.add(seed)
            logging.debug(
                f"The request {request} is skipped as {self.max_requests_per_seed} "
                f"max requests per seed have been reached for seed {seed}."
            )
            assert self.crawler.stats
            self.crawler.stats.set_value(
                "seeds/max_requests_reached", len(self.seeds_reached_limit)
            )
            raise IgnoreRequest("max_requests_per_seed_reached")
        self.requests_per_seed[seed] += 1
        return

    def max_requests_per_seed_reached(self, seed: str) -> bool:
        return self.requests_per_seed.get(seed, 0) >= self.max_requests_per_seed


class TrackSeedsSpiderMiddleware:
    def __init__(self, crawler: Crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    def process_start_requests(
        self, start_requests: Iterable[Request], spider: Spider
    ) -> Iterable[Request]:
        for request in start_requests:
            request.meta.setdefault("seed", request.url)
            request.meta.setdefault("is_seed_request", True)
            yield request

    def process_spider_output(
        self,
        response: Response,
        result: Iterable[Union[Request, Item]],
        spider: Spider,
    ) -> Iterable[Union[Request, Item]]:
        for item_or_request in result:
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            yield from self._process_request(item_or_request, response)

    async def process_spider_output_async(
        self,
        response: Response,
        result: AsyncIterable[Union[Request, Item]],
        spider: Spider,
    ) -> AsyncIterable[Union[Request, Item]]:
        async for item_or_request in result:
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            for processed_request in self._process_request(item_or_request, response):
                yield processed_request

    def _process_request(
        self, request: Request, response: Response
    ) -> Iterable[Request]:
        seed = request.meta.get("seed", response.meta.get("seed"))
        if seed is None:
            # we don't want to add a seed meta key with None if it is not in meta
            yield request
            return

        request.meta["seed"] = seed
        yield request


class PageParamsMiddlewareBase:
    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_start_requests(
        self, start_requests: List[Request], spider: Spider
    ) -> Iterable[Request]:
        for request in start_requests:
            self._update_page_params(request)
            yield request

    def process_spider_output(
        self, response, result, spider
    ) -> Iterable[Union[Request, Item]]:
        for item_or_request in result:
            if isinstance(item_or_request, Request):
                self._update_page_params(item_or_request)
            yield item_or_request

    async def process_spider_output_async(
        self, response, result, spider
    ) -> AsyncIterable[Union[Request, Item]]:
        async for item_or_request in result:
            if isinstance(item_or_request, Request):
                self._update_page_params(item_or_request)
            yield item_or_request

    def _update_page_params(self, request) -> None:
        page_params = request.meta.setdefault("page_params", {})
        self.update_page_params(request, page_params)

    def update_page_params(self, request, page_params) -> None:
        pass


class TrackNavigationDepthSpiderMiddleware(PageParamsMiddlewareBase):
    """
    This middleware helps manage navigation depth by setting a `final_navigation_page` meta key
    when the predefined depth limit (`NAVIGATION_DEPTH_LIMIT`) is reached.

    .. note::
        Navigation depth is typically increased for requests that navigate to a subcategory
        originating from its parent category, such as a request targeting a category starting
        from the website home page. However, it may not be necessary to increase navigation
        depth, for example, for the next pagination requests.
        Spiders can customize this behavior as needed by controlling when navigation depth is incremented.
    """

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        if max_navigation_depth := max(
            crawler.spider.settings.getint("NAVIGATION_DEPTH_LIMIT", 0), 0
        ):
            self.max_navigation_depth = max_navigation_depth
            self.stats = crawler.stats
        else:
            raise NotConfigured

    def update_page_params(self, request, page_params) -> None:
        page_params["skip_subcategories"] = request.meta.get(
            "final_navigation_page", page_params.get("skip_subcategories")
        )

    def process_start_requests(
        self, start_requests: List[Request], spider: Spider
    ) -> Iterable[Request]:
        for request in super().process_start_requests(start_requests, spider):
            # We treat the initial response as having a navigation_depth of 1.
            self._update_request_with_navigation(request, navigation_depth=1)
            self.stats.inc_value("navigation_depth/inits")
            yield request

    def process_spider_output(
        self, response, result, spider
    ) -> Iterable[Union[Request, Item]]:
        for item_or_request in super().process_spider_output(response, result, spider):
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            if req := self._process_navigation_depth(item_or_request, response):
                yield req

    async def process_spider_output_async(
        self, response, result, spider
    ) -> AsyncIterable[Union[Request, Item]]:
        async for item_or_request in super().process_spider_output_async(
            response, result, spider
        ):
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            if req := self._process_navigation_depth(item_or_request, response):
                yield req

    def _update_request_with_navigation(self, request, navigation_depth):
        if navigation_depth is None:
            return
        request.meta["navigation_depth"] = navigation_depth
        request.meta["final_navigation_page"] = (
            navigation_depth >= self.max_navigation_depth
        )

    def _current_navigation_depth(
        self, increase_navigation_depth, current_navigation_depth
    ):
        if increase_navigation_depth and current_navigation_depth is None:
            current_navigation_depth = 1
        return current_navigation_depth

    def _process_navigation_depth(self, request, response) -> Optional[Request]:
        increase_navigation_depth = request.meta.get("increase_navigation_depth", True)
        current_navigation_depth = self._current_navigation_depth(
            increase_navigation_depth, response.meta.get("navigation_depth")
        )

        if not increase_navigation_depth:
            self._update_request_with_navigation(request, current_navigation_depth)

            self.stats.inc_value("navigation_depth/not_counted")
            return request

        self.stats.inc_value(f"navigation_depth/count/{current_navigation_depth}")

        self.stats.max_value("navigation_depth/max_seen", current_navigation_depth)
        self._update_request_with_navigation(request, current_navigation_depth + 1)

        return request


class OnlyFeedsMiddleware(PageParamsMiddlewareBase):
    """
    This middleware helps control whether the spider should discover all links on the webpage
    or extract links from RSS/Atom feeds only.
    """

    def __init__(self, crawler: Crawler):
        super().__init__(crawler)
        assert crawler.spider
        if not crawler.spider.settings.getbool("ONLY_FEEDS_ENABLED"):  # type: ignore[union-attr]
            raise NotConfigured

    def update_page_params(self, request, page_params) -> None:
        page_params["only_feeds"] = request.meta.get(
            "only_feeds", page_params.get("only_feeds", True)
        )


class OffsiteRequestsPerSeedMiddleware:
    """This middleware ensures that subsequent requests for each seed do not go outside
    the original seed's domain.

    However, offsite requests are allowed only if it came from the original domain. Any
    other offsite requests that follow from offsite responses will not be allowed. This
    behavior allows to crawl articles from news aggregator websites while ensuring it
    doesn't fully crawl other domains it discover.

    Disabling the middleware would not prevent offsite requests from being filtered
    and might generally lead in other domains from being crawled completely, unless
    ``allowed_domains`` is set in the spider.

    This middleware relies on :class:`~zyte_spider_templates.TrackSeedsSpiderMiddleware`
    to set the `"seed"` and `"is_seed_request"` values in
    :attr:`Request.meta <scrapy.http.Request.meta>`. Ensure that such middleware is
    active and sets the said values before this middleware processes the spiders outputs.

    .. note::

        If a seed URL gets redirected to a different domain, both the domain from
        the original request and the domain from the redirected response will be
        used as references.

        If the seed URL is `https://books.toscrape.com`, all subsequent requests to
        `books.toscrape.com` and its subdomains are allowed, but requests to
        `toscrape.com` are not. Conversely, if the seed URL is `https://toscrape.com`,
        requests to both `toscrape.com` and `books.toscrape.com` are allowed.
    """

    def __init__(self, crawler: Crawler):
        assert crawler.spider
        if not crawler.spider.settings.getbool(  # type: ignore[union-attr]
            "OFFSITE_REQUESTS_PER_SEED_ENABLED", True
        ):
            raise NotConfigured

        self.stats = crawler.stats
        self.allowed_domains_per_seed: Dict[str, Set[str]] = defaultdict(set)
        self.domains_seen: Set[str] = set()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_spider_output(
        self,
        response: Response,
        result: Iterable[Union[Request, Item]],
        spider: Spider,
    ) -> Iterable[Union[Request, Item]]:
        self._fill_allowed_domains_per_seed_dict(response)
        for item_or_request in result:
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            if self.allow_request(item_or_request, response):
                yield item_or_request

    async def process_spider_output_async(
        self,
        response: Response,
        result: AsyncIterable[Union[Request, Item]],
        spider: Spider,
    ) -> AsyncIterable[Union[Request, Item]]:
        self._fill_allowed_domains_per_seed_dict(response)
        async for item_or_request in result:
            if not isinstance(item_or_request, Request):
                yield item_or_request
                continue

            if self.allow_request(item_or_request, response):
                yield item_or_request

    def allow_request(self, request: Request, response: Response) -> bool:
        if request.dont_filter:
            return True

        if self._is_domain_per_seed_allowed(request):
            return True
        elif self._is_domain_per_seed_allowed(response):
            # At this point, we know that the request points to an offsite page.
            # We don't want to immediately filter it as it might be an article from news
            # aggregator websites. So, we simply check if the request came from the
            # original website. Otherwise, it came from offsite pages and we avoid it.
            return True

        domain = urlparse_cached(request).hostname
        assert self.stats
        if domain and domain not in self.domains_seen:
            self.domains_seen.add(domain)
            self.stats.inc_value("offsite_requests_per_seed/domains")
        self.stats.inc_value("offsite_requests_per_seed/filtered")

        logger.debug(f"Filtered offsite request per seed to {domain}: {request}")
        return False

    def _fill_allowed_domains_per_seed_dict(self, response: Response) -> None:
        seed = response.meta.get("seed")
        if seed is None:
            return

        if not response.meta.get("is_seed_request"):
            if domains_for_update := response.meta.get("seed_domains"):
                self.allowed_domains_per_seed[seed].update(domains_for_update)
            return

        domains_for_update = response.meta.get(
            "seed_domains", self._get_allowed_domains(response)
        )
        self.allowed_domains_per_seed[seed].update(domains_for_update)

    def _is_domain_per_seed_allowed(
        self, req_or_resp: Union[Request, Response]
    ) -> bool:
        seed = req_or_resp.meta.get("seed")
        if seed is None:
            return True

        if allowed_domains := self.allowed_domains_per_seed.get(seed):
            return url_is_from_any_domain(req_or_resp.url, allowed_domains)

        return False

    def _get_allowed_domains(self, response: Response) -> Set[str]:
        """
        Returns the domains based on the URL attributes of items from a response and the originating request.

        In cases where the original request URL was redirected to a new domain,
        the new domain would be included as well.
        """

        def get_item_and_request_urls() -> Generator[str, None, None]:
            """Since the redirected URL and canonicalUrl are only in the Item,
            we try to extract it from the first item encountered."""
            for _, maybe_item in response.cb_kwargs.items():
                if isinstance(maybe_item, DynamicDeps):
                    for item_class in [Article, ArticleNavigation]:
                        if item := maybe_item.get(item_class):
                            for url_type in ("canonicalUrl", "url"):
                                if url := getattr(item, url_type, None):
                                    yield url
                            break
                    else:
                        logger.debug(
                            f"This type of item: {type(maybe_item)} is not allowed"
                        )
            assert response.request
            yield response.request.url

        return {get_domain(url) for url in get_item_and_request_urls()}


class DummyDupeFilter(RFPDupeFilter):
    """
    This class overrides the `request_seen` method to return `False` for all requests,
    disabling Scrapy's built-in duplicate filtering. Instead, deduplication
    is performed in `DupeFilterDownloaderMiddleware` before requests are passed to other
    middlewares.
    """

    def request_seen(self, request: Request) -> bool:
        return False


class DupeFilterSpiderMiddleware:
    """
    This middleware uses a custom duplicate filter to override Scrapy's default filtering,
    leveraging the `DummyDupeFilter` to bypass global deduplication. Instead,
    deduplication is managed within the middleware itself, filtering out duplicate requests
    before they reach other middlewares.
    """

    dupe_filter: RFPDupeFilter = RFPDupeFilter()

    def __init__(self, crawler):
        self.crawler = crawler

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_start_requests(
        self, start_requests: List[Request], spider: Spider
    ) -> Iterable[Request]:
        for request in start_requests:
            if not self.url_already_seen(None, request):
                yield request

    def process_spider_output(
        self, response, result, spider
    ) -> Iterable[Union[Request, Item]]:
        for item_or_request in result:
            if isinstance(item_or_request, Request):
                if not self.url_already_seen(response, item_or_request):
                    yield item_or_request
            else:
                yield item_or_request

    async def process_spider_output_async(
        self, response, result, spider
    ) -> AsyncIterable[Union[Request, Item]]:
        async for item_or_request in result:
            if isinstance(item_or_request, Request):
                if not self.url_already_seen(response, item_or_request):
                    yield item_or_request
            else:
                yield item_or_request

    def url_already_seen(self, response: Optional[Response], request: Request) -> bool:
        """A custom replacement for the default duplicate filtering, tracking URLs seen in this run."""
        if not request.dont_filter and self.dupe_filter.request_seen(request):
            logger.debug(
                f"URL is duplicated {request.url}, for the response {response.url if response else 'start_request'}."
            )
            self.crawler.stats.inc_value("dupe_filter_spider_mw/url_already_seen")
            return True
        return False
