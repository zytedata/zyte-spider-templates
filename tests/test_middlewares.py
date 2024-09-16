import pytest
from freezegun import freeze_time
from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.statscollectors import StatsCollector
from scrapy.utils.misc import create_instance
from scrapy.utils.test import get_crawler

from zyte_spider_templates.middlewares import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
)


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
    custom_request_fp = request_fingerprint(custom_request)
    unknown_request_fp = request_fingerprint(unknown_request)

    def results_gen():
        yield product_request
        yield next_page_request
        yield subcategory_request
        yield product_navigation_request
        yield product_navigation_heuristics_request
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

    result = list(middleware.process_spider_output(Response(""), [req], spider))
    if allowed:
        assert result == [req]
    else:
        assert result == []
