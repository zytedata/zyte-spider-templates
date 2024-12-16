import logging
from collections import defaultdict
from typing import Iterable, Union
from unittest.mock import MagicMock

import pytest
from freezegun import freeze_time
from pytest_twisted import ensureDeferred
from scrapy import Spider
from scrapy.exceptions import IgnoreRequest, NotConfigured
from scrapy.http import Request, Response
from scrapy.settings import Settings
from scrapy.statscollectors import StatsCollector
from scrapy.utils.misc import create_instance
from scrapy.utils.test import get_crawler
from scrapy_poet import DynamicDeps
from zyte_common_items import Article, Item, Product

from zyte_spider_templates.middlewares import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
    DummyDupeFilter,
    DupeFilterSpiderMiddleware,
    MaxRequestsPerSeedDownloaderMiddleware,
    OffsiteRequestsPerSeedMiddleware,
    OnlyFeedsMiddleware,
    PageParamsMiddlewareBase,
    TrackNavigationDepthSpiderMiddleware,
    TrackSeedsSpiderMiddleware,
)

from . import get_crawler as get_crawler_with_settings


def get_fingerprinter(crawler):
    return lambda request: crawler.request_fingerprinter.fingerprint(request).hex()


@freeze_time("2023-10-10 20:09:29")
def test_crawling_logs_middleware_no_requests():
    crawler = get_crawler()
    middleware = create_instance(
        CrawlingLogsMiddleware, settings=crawler.settings, crawler=crawler
    )

    url = "https://example.com"
    request = Request(url)
    response = Response(url=url, request=request)

    request_fingerprint = get_fingerprinter(crawler)
    fingerprint = request_fingerprint(request)

    def results_gen():
        return

    crawl_logs = middleware.crawl_logs(response, results_gen())
    assert crawl_logs == (
        "Crawling Logs for https://example.com (parsed as: None):\n"
        "Nothing to crawl.\n"
        "Structured Logs:\n"
        "{\n"
        '  "time": "2023-10-10 20:09:29",\n'
        '  "current": {\n'
        '    "url": "https://example.com",\n'
        '    "request_url": "https://example.com",\n'
        f'    "request_fingerprint": "{fingerprint}",\n'
        '    "page_type": null,\n'
        '    "probability": null\n'
        "  },\n"
        '  "to_crawl": {}\n'
        "}"
    )


@freeze_time("2023-10-10 20:09:29")
def test_crawling_logs_middleware():
    crawler = get_crawler()
    middleware = create_instance(
        CrawlingLogsMiddleware, settings=crawler.settings, crawler=crawler
    )

    url = "https://example.com"
    request = Request(url)
    response = Response(url=url, request=request)

    product_request = Request(
        "https://example.com/tech/products?id=1",
        priority=199,
        meta={
            "crawling_logs": {
                "name": "Product ID 1",
                "probability": 0.9951,
                "page_type": "product",
            },
        },
    )
    next_page_request = Request(
        "https://example.com?page=2",
        priority=100,
        meta={
            "crawling_logs": {
                "name": "Category Page 2",
                "probability": 0.9712,
                "page_type": "nextPage",
            },
        },
    )
    subcategory_request = Request(
        "https://example.com/tech/products/monitors",
        priority=98,
        meta={
            "crawling_logs": {
                "name": "Monitors Subcategory",
                "probability": 0.9817,
                "page_type": "subCategories",
            },
        },
    )
    product_navigation_request = Request(
        "https://example.com/books/products",
        priority=91,
        meta={
            "crawling_logs": {
                "name": "Books Category",
                "probability": 0.9136,
                "page_type": "productNavigation",
            },
        },
    )
    product_navigation_heuristics_request = Request(
        "https://example.com/some-other-page",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Some Other Page",
                "probability": 0.1,
                "page_type": "productNavigation-heuristics",
            },
        },
    )
    article_request = Request(
        "https://example.com/article_1",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Article 1",
                "probability": 0.1,
                "page_type": "article",
            },
        },
    )
    article_navigation_request = Request(
        "https://example.com/article_navigation_1",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Article Navigation 1",
                "probability": 0.1,
                "page_type": "articleNavigation",
            },
        },
    )
    article_navigation_heuristics_request = Request(
        "https://example.com/article_and_navigation_1",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Article And Navigation 1",
                "probability": 0.1,
                "page_type": "articleNavigation-heuristics",
            },
        },
    )
    job_posting_request = Request(
        "https://example.com/job_1",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Job Posting 1",
                "probability": 0.1,
                "page_type": "jobPosting",
            },
        },
    )
    job_posting_navigation_request = Request(
        "https://example.com/job_navigation_1",
        priority=10,
        meta={
            "crawling_logs": {
                "name": "Job Posting Navigation 1",
                "probability": 0.1,
                "page_type": "jobPostingNavigation",
            },
        },
    )
    custom_request = Request(
        "https://example.com/custom-page-type",
        meta={
            "crawling_logs": {
                "name": "Custom Page",
                "page_type": "some other page_type",
                "foo": "bar",
            },
        },
    )
    unknown_request = Request(
        "https://example.com/other-unknown",
    )

    request_fingerprint = get_fingerprinter(crawler)
    fingerprint = request_fingerprint(request)
    product_request_fp = request_fingerprint(product_request)
    next_page_request_fp = request_fingerprint(next_page_request)
    subcategory_request_fp = request_fingerprint(subcategory_request)
    product_navigation_request_fp = request_fingerprint(product_navigation_request)
    product_navigation_heuristics_request_fp = request_fingerprint(
        product_navigation_heuristics_request
    )
    job_posting_request_fp = request_fingerprint(job_posting_request)
    job_posting_navigation_request_fp = request_fingerprint(
        job_posting_navigation_request
    )
    custom_request_fp = request_fingerprint(custom_request)
    article_request_fp = request_fingerprint(article_request)
    article_navigation_request_fp = request_fingerprint(article_navigation_request)
    article_navigation_heuristics_request_fp = request_fingerprint(
        article_navigation_heuristics_request
    )
    custom_request_fp = request_fingerprint(custom_request)
    unknown_request_fp = request_fingerprint(unknown_request)

    def results_gen():
        yield product_request
        yield next_page_request
        yield subcategory_request
        yield product_navigation_request
        yield product_navigation_heuristics_request
        yield article_request
        yield article_navigation_request
        yield article_navigation_heuristics_request
        yield job_posting_request
        yield job_posting_navigation_request
        yield custom_request
        yield unknown_request

    crawl_logs = middleware.crawl_logs(response, results_gen())
    assert crawl_logs == (
        "Crawling Logs for https://example.com (parsed as: None):\n"
        "Number of Requests per page type:\n"
        "- product: 1\n"
        "- nextPage: 1\n"
        "- subCategories: 1\n"
        "- productNavigation: 1\n"
        "- productNavigation-heuristics: 1\n"
        "- article: 1\n"
        "- articleNavigation: 1\n"
        "- articleNavigation-heuristics: 1\n"
        "- jobPosting: 1\n"
        "- jobPostingNavigation: 1\n"
        "- some other page_type: 1\n"
        "- unknown: 1\n"
        "Structured Logs:\n"
        "{\n"
        '  "time": "2023-10-10 20:09:29",\n'
        '  "current": {\n'
        '    "url": "https://example.com",\n'
        '    "request_url": "https://example.com",\n'
        f'    "request_fingerprint": "{fingerprint}",\n'
        '    "page_type": null,\n'
        '    "probability": null\n'
        "  },\n"
        '  "to_crawl": {\n'
        '    "product": [\n'
        "      {\n"
        '        "name": "Product ID 1",\n'
        '        "probability": 0.9951,\n'
        '        "page_type": "product",\n'
        '        "request_url": "https://example.com/tech/products?id=1",\n'
        '        "request_priority": 199,\n'
        f'        "request_fingerprint": "{product_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "nextPage": [\n'
        "      {\n"
        '        "name": "Category Page 2",\n'
        '        "probability": 0.9712,\n'
        '        "page_type": "nextPage",\n'
        '        "request_url": "https://example.com?page=2",\n'
        '        "request_priority": 100,\n'
        f'        "request_fingerprint": "{next_page_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "subCategories": [\n'
        "      {\n"
        '        "name": "Monitors Subcategory",\n'
        '        "probability": 0.9817,\n'
        '        "page_type": "subCategories",\n'
        '        "request_url": "https://example.com/tech/products/monitors",\n'
        '        "request_priority": 98,\n'
        f'        "request_fingerprint": "{subcategory_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "productNavigation": [\n'
        "      {\n"
        '        "name": "Books Category",\n'
        '        "probability": 0.9136,\n'
        '        "page_type": "productNavigation",\n'
        '        "request_url": "https://example.com/books/products",\n'
        '        "request_priority": 91,\n'
        f'        "request_fingerprint": "{product_navigation_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "productNavigation-heuristics": [\n'
        "      {\n"
        '        "name": "Some Other Page",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "productNavigation-heuristics",\n'
        '        "request_url": "https://example.com/some-other-page",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{product_navigation_heuristics_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "article": [\n'
        "      {\n"
        '        "name": "Article 1",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "article",\n'
        '        "request_url": "https://example.com/article_1",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{article_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "articleNavigation": [\n'
        "      {\n"
        '        "name": "Article Navigation 1",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "articleNavigation",\n'
        '        "request_url": "https://example.com/article_navigation_1",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{article_navigation_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "articleNavigation-heuristics": [\n'
        "      {\n"
        '        "name": "Article And Navigation 1",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "articleNavigation-heuristics",\n'
        '        "request_url": "https://example.com/article_and_navigation_1",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{article_navigation_heuristics_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "jobPosting": [\n'
        "      {\n"
        '        "name": "Job Posting 1",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "jobPosting",\n'
        '        "request_url": "https://example.com/job_1",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{job_posting_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "jobPostingNavigation": [\n'
        "      {\n"
        '        "name": "Job Posting Navigation 1",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "jobPostingNavigation",\n'
        '        "request_url": "https://example.com/job_navigation_1",\n'
        '        "request_priority": 10,\n'
        f'        "request_fingerprint": "{job_posting_navigation_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "some other page_type": [\n'
        "      {\n"
        '        "name": "Custom Page",\n'
        '        "page_type": "some other page_type",\n'
        '        "foo": "bar",\n'
        '        "request_url": "https://example.com/custom-page-type",\n'
        '        "request_priority": 0,\n'
        f'        "request_fingerprint": "{custom_request_fp}"\n'
        "      }\n"
        "    ],\n"
        '    "unknown": [\n'
        "      {\n"
        '        "request_url": "https://example.com/other-unknown",\n'
        '        "request_priority": 0,\n'
        f'        "request_fingerprint": "{unknown_request_fp}"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}"
    )


def test_crawling_logs_middleware_deprecated_subclassing():
    class CustomCrawlingLogsMiddleware(CrawlingLogsMiddleware):
        def __init__(self):
            pass

    crawler = get_crawler()
    with pytest.warns(DeprecationWarning, match="must now accept a crawler parameter"):
        middleware = create_instance(
            CustomCrawlingLogsMiddleware, settings=crawler.settings, crawler=crawler
        )
    assert middleware._crawler == crawler
    assert hasattr(middleware, "_fingerprint")


@pytest.mark.parametrize(
    "req,allowed",
    (
        (Request("https://example.com"), True),
        (Request("https://outside-example.com"), False),
        (Request("https://outside-example.com", meta={"allow_offsite": True}), True),
    ),
)
def test_item_offsite_middleware(req, allowed):
    class TestSpider(Spider):
        name = "test"
        allowed_domains = ("example.com",)

    spider = TestSpider()
    crawler = get_crawler(TestSpider)
    stats = StatsCollector(crawler)
    middleware = AllowOffsiteMiddleware(stats)
    middleware.spider_opened(spider)

    assert middleware.should_follow(req, spider) == allowed


@pytest.fixture
def mock_crawler():
    mock_settings = MagicMock(spec=Settings)
    mock_crawler = MagicMock(spec=["spider", "settings"])
    mock_crawler.settings = mock_settings
    return mock_crawler


@pytest.mark.parametrize("max_requests_per_seed", [10, "10", -10, False, None])
def test_middleware_init(mock_crawler, max_requests_per_seed):
    class TestSpider(Spider):
        name = "test"
        allowed_domains = ("example.com",)
        settings = Settings({"MAX_REQUESTS_PER_SEED": max_requests_per_seed})

    crawler = get_crawler(TestSpider)
    crawler.spider = TestSpider()
    if max_requests_per_seed not in [-10, False, None]:
        middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
        assert middleware.max_requests_per_seed == int(max_requests_per_seed)
    else:
        with pytest.raises(NotConfigured):
            MaxRequestsPerSeedDownloaderMiddleware(crawler)


@pytest.mark.parametrize(
    "seed, requests_per_seed, max_requests_per_seed, expected_result",
    [
        (
            "http://example.com",
            2,
            5,
            False,
        ),  # Request count below max_requests_per_seed
        (
            "http://example.com",
            2,
            2,
            True,
        ),  # Request count equal to max_requests_per_seed
        (
            "http://example.com",
            5,
            2,
            True,
        ),  # Request count above to max_requests_per_seed
    ],
)
def test_max_requests_per_seed_reached(
    mock_crawler, seed, requests_per_seed, max_requests_per_seed, expected_result
):
    mock_crawler.spider.settings = Settings(
        {"MAX_REQUESTS_PER_SEED": max_requests_per_seed}
    )
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(mock_crawler)
    downloader_middleware.requests_per_seed = defaultdict()
    downloader_middleware.requests_per_seed[seed] = requests_per_seed

    assert downloader_middleware.max_requests_per_seed_reached(seed) == expected_result


def _get_seed_crawler():
    class TestSpiderSeed(Spider):
        name = "test_seed"

    crawler = get_crawler(TestSpiderSeed)
    crawler.spider = TestSpiderSeed()
    crawler.spider.settings = Settings({"MAX_REQUESTS_PER_SEED": 2})
    return crawler


def test_process_request():
    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"
    request_url_3 = "https://example.com/3"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    assert downloader_middleware.crawler == crawler
    assert isinstance(
        downloader_middleware.from_crawler(crawler),
        MaxRequestsPerSeedDownloaderMiddleware,
    )
    assert isinstance(
        spider_middleware.from_crawler(crawler), TrackSeedsSpiderMiddleware
    )

    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    request = Request(url=request_url_1)
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == request_url_1
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {request_url_1: 1}

    response = Response(url=request_url_1, request=request)
    request = Request(url=request_url_2)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == request_url_1
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {request_url_1: 2}

    # After reaching the max request for the given seed, requests would be filtered.
    response = Response(url=request_url_2, request=request)
    request = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == request_url_1
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {request_url_1: 2}


def test_process_request_seed_override():
    """This tests the scenario when the 'seed' in the request.meta is overridden in the
    start_requests() method.
    """

    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"
    request_url_3 = "https://example.com/3"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    seed = "some non-url key"

    request = Request(url=request_url_1, meta={"seed": seed})
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    response = Response(url=request_url_1, request=request)
    request = Request(url=request_url_2)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}

    # After reaching the max request for the given seed, requests would be filtered.

    response = Response(url=request_url_2, request=request)
    request = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}


def test_process_request_seed_override_2():
    """Similar to test_process_request_seed_override() but instead of overridding the
    'seed' value in the start_requests(), it's in one of the callbacks.
    """

    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"
    request_url_3 = "https://example.com/3"
    request_url_4 = "https://example.com/4"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    seed_1 = "some non-url key"
    seed_2 = "another non-url key"

    request_1 = Request(url=request_url_1, meta={"seed": seed_1})
    request_gen = spider_middleware.process_start_requests([request_1], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == seed_1
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed_1: 1}

    # This request coming from a callback uses a new seed value.

    response = Response(url=request_url_1, request=request_1)
    request_2 = Request(url=request_url_2, meta={"seed": seed_2})
    request_gen = spider_middleware.process_spider_output(
        response, [request_2], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed_2
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed_1: 1, seed_2: 1}

    response = Response(url=request_url_2, request=request_2)
    request_3 = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request_3], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed_2
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed_1: 1, seed_2: 2}

    # After reaching the max request for the 2nd seed, requests would be filtered.

    response = Response(url=request_url_3, request=request_3)
    request_4 = Request(url=request_url_4)
    request_gen = spider_middleware.process_spider_output(
        response, [request_4], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed_2
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed_1: 1, seed_2: 2}


def test_process_request_seed_override_multiple():
    """Similar to test_process_request_seed_override() but multiple start requests
    point to the same seed.
    """

    request_url_1 = "https://us.example.com/1"
    request_url_2 = "https://fr.example.com/1"
    request_url_3 = "https://us.example.com/2"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    seed = "some non-url key"

    request = Request(url=request_url_1, meta={"seed": seed})
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    request = Request(url=request_url_2, meta={"seed": seed})
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}

    # After reaching the max request for the given seed, requests would be filtered.

    response = Response(url=request_url_1, request=request)
    request = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}


def test_process_request_seed_override_downstream():
    """This tests the scenario when the 'seed' in the request.meta is overridden in the
    start_requests() method, but an unrelated request downstream from another domain
    uses the same custom 'seed' value.
    """

    request_url_1 = "https://example.com/1"
    request_url_2 = "https://another-example.com/1"
    request_url_3 = "https://example.com/2"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    seed = "some non-url key"

    request = Request(url=request_url_1, meta={"seed": seed})
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    response = Response(url=request_url_1, request=request)
    request = Request(url=request_url_2, meta={"seed": seed})
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}

    # After reaching the max request for the given seed, requests would be filtered.

    response = Response(url=request_url_2, request=request)
    request = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}


def test_process_request_seed_override_remove():
    """This tests the scenario when the 'seed' in the request.meta is overridden in the
    start_requests() method, but one of the request explicitly sets the 'seed' to None.
    """

    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"  # This one removes the 'seed' in meta
    request_url_3 = "https://example.com/3"
    request_url_4 = "https://example.com/4"
    request_url_5 = "https://example.com/5"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]

    seed = "some non-url key"

    request_1: Request = Request(url=request_url_1, meta={"seed": seed})
    request_gen = spider_middleware.process_start_requests([request_1], crawler.spider)
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert request.meta["seed"] == seed
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    response = Response(url=request_url_1, request=request_1)
    request_2: Union[Request, Item] = Request(url=request_url_2, meta={"seed": None})
    request_gen = spider_middleware.process_spider_output(
        response, [request_2], crawler.spider
    )
    request_2 = list(request_gen)[0]
    assert isinstance(request_2, Request)
    assert request_2.meta["seed"] is None
    downloader_middleware.process_request(request_2, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    # A request coming from the request which sets 'seed' to None won't have a sticky
    # 'seed' value.

    response = Response(url=request_url_1, request=request_2)
    request_3: Union[Request, Item] = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request_3], crawler.spider
    )
    request_3 = list(request_gen)[0]
    assert isinstance(request_3, Request)
    assert "seed" not in request_3.meta
    downloader_middleware.process_request(request_3, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 1}

    # However, a request coming from the untampered 'seed' value would still have the
    # stick 'seed' value.

    response = Response(url=request_url_1, request=request_1)
    request_4: Union[Request, Item] = Request(url=request_url_4)
    request_gen = spider_middleware.process_spider_output(
        response, [request_4], crawler.spider
    )
    request_4 = list(request_gen)[0]
    assert isinstance(request_4, Request)
    assert request_4.meta["seed"] == seed
    downloader_middleware.process_request(request_4, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}

    # Eventually, the stick 'seed' would result in filtered requests

    response = Response(url=request_url_5, request=request_4)
    request_5: Union[Request, Item] = Request(url=request_url_5)
    request_gen = spider_middleware.process_spider_output(
        response, [request_5], crawler.spider
    )
    request_5 = list(request_gen)[0]
    assert isinstance(request_5, Request)
    assert request.meta["seed"] == seed
    with pytest.raises(IgnoreRequest):
        downloader_middleware.process_request(request_5, crawler.spider)
    assert downloader_middleware.requests_per_seed == {seed: 2}


def test_process_request_seed_none():
    """The user sets the 'seed' meta to None in the start_requests() method.

    This essentially disables the middleware and the 'MAX_REQUESTS_PER_SEED' setting has
    no effect.
    """

    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"
    request_url_3 = "https://example.com/3"

    crawler = _get_seed_crawler()
    spider_middleware = TrackSeedsSpiderMiddleware(crawler)
    downloader_middleware = MaxRequestsPerSeedDownloaderMiddleware(crawler)
    request_gen: Iterable[Union[Request, Item]]
    request: Union[Request, Item]

    request = Request(url=request_url_1, meta={"seed": None})
    request_gen = spider_middleware.process_start_requests([request], crawler.spider)
    request = list(request_gen)[0]
    assert request.meta["seed"] is None
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {}

    response = Response(url=request_url_1, request=request)
    request = Request(url=request_url_2)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert "seed" not in request.meta
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {}

    # Unlike the other tests above, the 3rd one pushes through since the
    # 'MAX_REQUESTS_PER_SEED' setting takes no effect.

    response = Response(url=request_url_2, request=request)
    request = Request(url=request_url_3)
    request_gen = spider_middleware.process_spider_output(
        response, [request], crawler.spider
    )
    request = list(request_gen)[0]
    assert isinstance(request, Request)
    assert "seed" not in request.meta
    downloader_middleware.process_request(request, crawler.spider)
    assert downloader_middleware.requests_per_seed == {}


def test_offsite_requests_per_seed_middleware_not_configured():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.spider.settings = Settings({"OFFSITE_REQUESTS_PER_SEED_ENABLED": False})
    with pytest.raises(NotConfigured):
        OffsiteRequestsPerSeedMiddleware(crawler)


def test_offsite_requests_per_seed_middleware():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    crawler.spider.settings = Settings({"OFFSITE_REQUESTS_PER_SEED_ENABLED": True})
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)

    # no result
    request = Request(url="https://example.com/1")
    response = Response(url=request.url, request=request)
    result = list(middleware.process_spider_output(response, [], crawler.spider))
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result == []
    assert middleware.allowed_domains_per_seed == {}
    assert "seed_url" not in request.meta

    # is_seed_request: True, domain allowed
    seed = "https://example.com/1"
    request = Request(
        url="https://example.com/1", meta={"is_seed_request": True, "seed": seed}
    )
    item = Article(url="https://example.com/article")
    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {
        "https://example.com/1": {"example.com"}
    }
    assert request.meta["seed"] == request.url

    # "seed" in meta, domain allowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    middleware.allowed_domains_per_seed = defaultdict(set, {seed: {"example.com"}})
    request = Request(url="https://example.com/2", meta={"seed": seed})

    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # "seed" in meta, domain disallowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(url="https://example_1.com/1", meta={"seed": seed})
    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {}
    assert request.meta["seed"] == seed

    # seed not in meta
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    request = Request(url="https://example.com/1")

    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {}
    assert "seed" not in request.meta
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")

    # "seed" in meta, seed_domains are in meta, seed_domain allowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(
        url="https://example_1.com/1",
        meta={"seed": seed, "seed_domains": {"example_1.com"}},
    )
    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example_1.com"}}
    assert request.meta["seed"] == seed

    # "seed" in meta, seed_domains are in meta, seed_domain disallowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(
        url="https://example_1.com/1",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    response = Response(url=request.url, request=request)
    result = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # Offsite request - 1st offsite request is NOT filtered out to extract article
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    seed_request = Request(
        url=seed,
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    seed_response = Response(url=seed, request=seed_request)
    request = Request(
        url="https://another-example.com",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    item = Article(url="https://another-example.com")
    result = list(
        middleware.process_spider_output(seed_response, [request, item], crawler.spider)
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") is None
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") is None
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # Offsite request - consequent offsite request are filtered out
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    prev_request = Request(
        url="https://another-example.com",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    prev_response = Response(url="https://another-example.com", request=prev_request)
    request = Request(
        url="https://another-example.com/page-2",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    result = list(
        middleware.process_spider_output(prev_response, [request, item], crawler.spider)
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed


@ensureDeferred
async def result_as_async_gen(middleware, response, result, spider):
    async def async_generator():
        for r in result:
            yield r

    processed_result = []
    async for processed_request in middleware.process_spider_output_async(
        response, async_generator(), spider
    ):
        processed_result.append(processed_request)
    return processed_result


@ensureDeferred
async def test_offsite_requests_per_seed_middleware_async():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    crawler.spider.settings = Settings({"OFFSITE_REQUESTS_PER_SEED_ENABLED": True})
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)

    # no result
    request = Request(url="https://example.com/1")
    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(middleware, response, [], crawler.spider)
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result == []
    assert middleware.allowed_domains_per_seed == {}
    assert "seed_url" not in request.meta

    # is_seed_request: True, domain allowed
    seed = "https://example.com/1"
    request = Request(
        url="https://example.com/1", meta={"is_seed_request": True, "seed": seed}
    )
    item = Article(url="https://example.com/article")
    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {
        "https://example.com/1": {"example.com"}
    }
    assert request.meta["seed"] == request.url

    # "seed" in meta, domain allowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    middleware.allowed_domains_per_seed = defaultdict(set, {seed: {"example.com"}})
    request = Request(url="https://example.com/2", meta={"seed": seed})

    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # "seed" in meta, domain disallowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(url="https://example_1.com/1", meta={"seed": seed})
    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {}
    assert request.meta["seed"] == seed

    # seed not in meta
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    request = Request(url="https://example.com/1")

    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {}
    assert "seed" not in request.meta
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")

    # "seed" in meta, seed_domains are in meta, seed_domain allowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(
        url="https://example_1.com/1",
        meta={"seed": seed, "seed_domains": {"example_1.com"}},
    )
    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert not crawler.stats.get_value("offsite_requests_per_seed/domains")
    assert not crawler.stats.get_value("offsite_requests_per_seed/filtered")
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example_1.com"}}
    assert request.meta["seed"] == seed

    # "seed" in meta, seed_domains are in meta, seed_domain disallowed
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    request = Request(
        url="https://example_1.com/1",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    response = Response(url=request.url, request=request)
    result = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # Offsite request - 1st offsite request is NOT filtered out to extract article
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    seed_request = Request(
        url=seed,
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    seed_response = Response(url=seed, request=seed_request)
    request = Request(
        url="https://another-example.com",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    item = Article(url="https://another-example.com")
    result = await result_as_async_gen(
        middleware, seed_response, [request, item], crawler.spider
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") is None
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") is None
    assert result[0] == request
    assert result[1] == item
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed

    # Offsite request - consequent offsite request are filtered out
    crawler.stats = StatsCollector(crawler)
    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    seed = "https://example.com/1"
    prev_request = Request(
        url="https://another-example.com",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    prev_response = Response(url="https://another-example.com", request=prev_request)
    request = Request(
        url="https://another-example.com/page-2",
        meta={"seed": seed, "seed_domains": {"example.com"}},
    )
    result = await result_as_async_gen(
        middleware, prev_response, [request, item], crawler.spider
    )
    assert crawler.stats.get_value("offsite_requests_per_seed/domains") == 1
    assert crawler.stats.get_value("offsite_requests_per_seed/filtered") == 1
    assert result == [item]
    assert middleware.allowed_domains_per_seed == {seed: {"example.com"}}
    assert request.meta["seed"] == seed


@pytest.mark.parametrize(
    "meta, expected_is_seed_request, expected_seed",
    [
        ({"is_seed_request": True}, True, "https://example.com/1"),
        ({"is_seed_request": False, "seed": "test_seed"}, False, "test_seed"),
        ({}, True, "https://example.com/1"),
    ],
)
def test_track_seeds_process_start_requests(
    meta, expected_is_seed_request, expected_seed
):
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    middleware = TrackSeedsSpiderMiddleware(crawler)
    assert isinstance(middleware.from_crawler(crawler), TrackSeedsSpiderMiddleware)

    start_request_url = "https://example.com/1"
    start_request = Request(url=start_request_url, meta=meta)
    result = list(middleware.process_start_requests([start_request], TestSpider()))
    assert result[0].meta["is_seed_request"] == expected_is_seed_request
    assert result[0].meta["seed"] == expected_seed


@pytest.mark.parametrize(
    "input_response, expected_urls",
    (
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://a.example",
                    cb_kwargs={
                        0: DynamicDeps({Article: Article(url="https://a.example")})  # type: ignore[dict-item]
                    },
                ),
            ),
            {"a.example"},
        ),
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://a.example",
                    cb_kwargs={
                        0: DynamicDeps({Article: Article(url="https://b.example")})  # type: ignore[dict-item]
                    },
                ),
            ),
            {"a.example", "b.example"},
        ),
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://a.example",
                    cb_kwargs={
                        0: DynamicDeps(
                            {
                                Article: Article(
                                    url="https://b.example",
                                    canonicalUrl="https://b.example",
                                )
                            }
                        )  # type: ignore[dict-item]
                    },
                ),
            ),
            {"a.example", "b.example"},
        ),
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://a.example",
                    cb_kwargs={
                        0: DynamicDeps(
                            {
                                Article: Article(
                                    url="https://b.example",
                                    canonicalUrl="https://c.example",
                                )
                            }
                        )  # type: ignore[dict-item]
                    },
                ),
            ),
            {"a.example", "b.example", "c.example"},
        ),
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://b.example",
                    cb_kwargs={
                        0: DynamicDeps(
                            {
                                Article: Article(
                                    url="https://c.example",
                                    canonicalUrl="https://d.example",
                                )
                            }
                        )  # type: ignore[dict-item]
                    },
                ),
            ),
            {"b.example", "c.example", "d.example"},
        ),
        (
            Response(
                url="https://a.example",
                request=Request(
                    url="https://b.example",
                    cb_kwargs={
                        0: DynamicDeps(
                            {
                                Product: Product(
                                    url="https://c.example",
                                    canonicalUrl="https://d.example",
                                )
                            }
                        )  # type: ignore[dict-item]
                    },
                ),
            ),
            {"b.example"},
        ),
    ),
)
def test_get_allowed_domains(input_response, expected_urls, caplog):
    class TestSpider(Spider):
        name = "test"

    caplog.clear()
    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    crawler.spider.settings = Settings({"OFFSITE_REQUESTS_PER_SEED_ENABLED": True})
    logging.getLogger().setLevel(logging.DEBUG)

    middleware = OffsiteRequestsPerSeedMiddleware(crawler)
    result = middleware._get_allowed_domains(input_response)

    assert result == expected_urls
    item = input_response.request.cb_kwargs[0]
    if Article not in input_response.request.cb_kwargs[0]:
        assert caplog.messages[-1] == f"This type of item: {type(item)} is not allowed"


def test_from_crawler():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()
    crawler.spider.settings = Settings({"OFFSITE_REQUESTS_PER_SEED_ENABLED": True})

    assert isinstance(
        OffsiteRequestsPerSeedMiddleware.from_crawler(crawler=crawler),
        OffsiteRequestsPerSeedMiddleware,
    )


def test_page_params_middleware_base():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()

    request_url = "https://example.com/1"
    request = Request(request_url)
    item = Article(url="https://example.com/article")
    response = Response(url=request_url, request=request)
    middleware = PageParamsMiddlewareBase(crawler)
    assert middleware.crawler == crawler
    assert isinstance(middleware.from_crawler(crawler), PageParamsMiddlewareBase)

    processed_output = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert processed_output[0].meta["page_params"] == {}  # type: ignore[union-attr]

    request = Request(url=request_url)
    processed_output = list(
        middleware.process_start_requests([request], crawler.spider)
    )
    assert processed_output[0].meta["page_params"] == {}  # type: ignore[union-attr]

    request = Request(request_url, meta={"page_params": {"test": 1}})
    response = Response(url=request_url, request=request)
    middleware = PageParamsMiddlewareBase(crawler)
    processed_output = list(
        middleware.process_spider_output(response, [request, item], crawler.spider)
    )
    assert processed_output[0].meta["page_params"] == {"test": 1}  # type: ignore[union-attr]

    processed_output = list(
        middleware.process_start_requests([request], crawler.spider)
    )
    assert processed_output[0].meta["page_params"] == {"test": 1}  # type: ignore[union-attr]


@ensureDeferred
async def test_page_params_middleware_base_async():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler()
    crawler.spider = TestSpider()

    # Default page_params value
    request_url = "https://example.com/1"
    request = Request(request_url)
    item = Article(url="https://example.com/article")
    response = Response(url=request_url, request=request)
    middleware = PageParamsMiddlewareBase(crawler)
    processed_output = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert processed_output[0].meta["page_params"] == {}
    assert processed_output[1] == item

    # Explicit page_params in request meta
    request = Request(request_url, meta={"page_params": {"test": 1}})
    response = Response(url=request_url, request=request)
    middleware = PageParamsMiddlewareBase(crawler)
    processed_output = await result_as_async_gen(
        middleware, response, [request, item], crawler.spider
    )
    assert processed_output[0].meta["page_params"] == {"test": 1}
    assert processed_output[1] == item


def test_only_feeds_middleware():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler_with_settings()
    crawler.spider = TestSpider()
    crawler.spider.settings = Settings({})

    # ONLY_FEEDS_ENABLED = True
    crawler.spider.settings.set("ONLY_FEEDS_ENABLED", True)
    middleware = OnlyFeedsMiddleware(crawler)
    assert middleware is not None

    # ONLY_FEEDS_ENABLED = False
    crawler.spider.settings.set("ONLY_FEEDS_ENABLED", False)
    with pytest.raises(NotConfigured):
        OnlyFeedsMiddleware(crawler)

    # Explicit only_feeds in request meta
    crawler.spider.settings.set("ONLY_FEEDS_ENABLED", True)
    middleware = OnlyFeedsMiddleware(crawler)

    request_url = "https://example.com/1"
    request = Request(request_url, meta={"only_feeds": False})

    page_params: dict = {}
    middleware.update_page_params(request, page_params)

    assert page_params["only_feeds"] is False

    # Default only_feeds value
    request = Request(request_url)
    page_params = {}
    middleware.update_page_params(request, page_params)

    assert page_params["only_feeds"] is True


def test_dummy_dupe_filter():
    request_url = "https://example.com/1"
    request = Request(request_url)
    middleware = DummyDupeFilter()
    assert middleware.request_seen(request) is False


def test_dupe_filter_spider_middleware():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler_with_settings()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    item = Article(url="https://example.com/article")

    middleware = DupeFilterSpiderMiddleware(crawler)
    assert middleware.crawler == crawler
    assert isinstance(middleware.from_crawler(crawler), DupeFilterSpiderMiddleware)

    # Test process_start_requests
    start_requests = [
        Request(url="https://example.com/1"),
        Request(url="https://example.com/2"),
    ]
    processed_requests = list(
        middleware.process_start_requests(start_requests, crawler.spider)
    )
    assert len(processed_requests) == 2

    # Simulate duplicate request
    start_requests = [
        Request(url="https://example.com/1"),
        Request(url="https://example.com/3"),
    ]
    processed_requests = list(
        middleware.process_start_requests(start_requests, crawler.spider)
    )
    assert len(processed_requests) == 1
    assert processed_requests[0].url == "https://example.com/3"

    # Test process_spider_output
    response = Response(url="https://example.com/1")
    result = [
        Request(url="https://example.com/4"),
        item,
        Request(url="https://example.com/1"),
    ]
    processed_output = list(
        middleware.process_spider_output(response, result, crawler.spider)
    )
    assert len(processed_output) == 2
    assert processed_output[0].url == "https://example.com/4"  # type: ignore[union-attr]
    assert processed_output[1] == item


@ensureDeferred
async def test_dupe_filter_spider_middleware_async():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler_with_settings()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    item = Article(url="https://example.com/article")

    middleware = DupeFilterSpiderMiddleware(crawler)

    assert middleware.crawler == crawler
    assert isinstance(middleware.from_crawler(crawler), DupeFilterSpiderMiddleware)

    # Test process_start_requests
    start_requests = [
        Request(url="https://example.com/11"),
        Request(url="https://example.com/21"),
    ]
    processed_requests = list(
        middleware.process_start_requests(start_requests, crawler.spider)
    )
    assert len(processed_requests) == 2

    # Simulate duplicate request
    start_requests = [
        Request(url="https://example.com/11"),
        Request(url="https://example.com/31"),
    ]
    processed_requests = list(
        middleware.process_start_requests(start_requests, crawler.spider)
    )
    assert len(processed_requests) == 1
    assert processed_requests[0].url == "https://example.com/31"

    # Test process_spider_output_async
    response = Response(url="https://example.com/11")
    processed_output = await result_as_async_gen(
        middleware,
        response,
        [
            Request(url="https://example.com/41"),
            item,
            Request(url="https://example.com/11"),
        ],
        crawler.spider,
    )

    assert len(processed_output) == 2
    assert processed_output[0].url == "https://example.com/41"
    assert processed_output[1] == item


def test_track_navigation_depth_spider_middleware():
    class TestSpider(Spider):
        name = "test"

    crawler = get_crawler_with_settings()
    crawler.spider = TestSpider()
    crawler.stats = StatsCollector(crawler)
    crawler.spider.settings = Settings({})
    request_url_1 = "https://example.com/1"
    request_url_2 = "https://example.com/2"
    item = Article(url="https://example.com/article")

    # NAVIGATION_DEPTH_LIMIT = 1
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 1)
    middleware = TrackNavigationDepthSpiderMiddleware(crawler)
    assert middleware is not None
    assert middleware.max_navigation_depth == 1

    assert isinstance(
        middleware.from_crawler(crawler), TrackNavigationDepthSpiderMiddleware
    )

    # NAVIGATION_DEPTH_LIMIT = 0
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 0)
    with pytest.raises(NotConfigured):
        TrackNavigationDepthSpiderMiddleware(crawler)

    # Explicit final_navigation_page in request meta
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 1)
    middleware = TrackNavigationDepthSpiderMiddleware(crawler)

    request = Request(request_url_1, meta={"final_navigation_page": True})
    page_params: dict = {}
    middleware.update_page_params(request, page_params)
    assert page_params["skip_subcategories"] is True

    # Default final_navigation_page value
    request = Request(request_url_1)
    page_params = {}
    middleware.update_page_params(request, page_params)
    assert page_params["skip_subcategories"] is None

    # Test process_start_requests with NAVIGATION_DEPTH_LIMIT = 1
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 1)
    middleware = TrackNavigationDepthSpiderMiddleware(crawler)
    processed_requests = list(
        middleware.process_start_requests(
            [Request(url=request_url_1), Request(url=request_url_2)], crawler.spider
        )
    )
    assert len(processed_requests) == 2
    for i in (0, 1):
        assert processed_requests[i].meta["final_navigation_page"] is True
        assert processed_requests[i].meta["navigation_depth"] == 1
        assert processed_requests[i].meta["page_params"] == {"skip_subcategories": None}

    # Test process_start_requests with NAVIGATION_DEPTH_LIMIT = 2
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 2)
    middleware = TrackNavigationDepthSpiderMiddleware(crawler)
    processed_requests = list(
        middleware.process_start_requests(
            [Request(url=request_url_1), Request(url=request_url_2)], crawler.spider
        )
    )
    assert len(processed_requests) == 2
    for i in (0, 1):
        assert processed_requests[i].meta["final_navigation_page"] is False
        assert processed_requests[i].meta["navigation_depth"] == 1
        assert processed_requests[i].meta["page_params"] == {"skip_subcategories": None}

    # Test process_spider_output
    crawler.spider.settings.set("NAVIGATION_DEPTH_LIMIT", 1)
    middleware = TrackNavigationDepthSpiderMiddleware(crawler)

    response = Response(url=request_url_1, request=Request(url=request_url_1, meta={}))
    result = [
        Request(url=request_url_1, meta={}),
        item,
        Request(url=request_url_2, meta={}),
    ]
    processed_output = list(
        middleware.process_spider_output(response, result, crawler.spider)
    )
    assert len(processed_output) == 3
    assert processed_output[0].url == request_url_1  # type: ignore[union-attr]
    assert processed_output[1] == item
    assert processed_output[2].url == request_url_2  # type: ignore[union-attr]
