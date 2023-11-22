import pytest
from freezegun import freeze_time
from scrapy import Spider
from scrapy.http import Request, Response
from scrapy.statscollectors import StatsCollector
from scrapy.utils.test import get_crawler

from zyte_spider_templates.middlewares import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
)


@freeze_time("2023-10-10 20:09:29")
def test_crawling_logs_middleware_no_requests():
    middleware = CrawlingLogsMiddleware()

    url = "https://example.com"
    request = Request(url)
    response = Response(url=url, request=request)

    def results_gen():
        return

    crawl_logs = middleware.crawl_logs(response, results_gen())
    assert crawl_logs == (
        "Crawling Logs for https://example.com (parsed as: None):\n"
        "Number of Requests per page type:\n"
        "- product: 0\n"
        "- nextPage: 0\n"
        "- subCategories: 0\n"
        "- productNavigation: 0\n"
        "- productNavigation-heuristics: 0\n"
        "- unknown: 0\n"
        "Structured Logs:\n"
        "{\n"
        '  "time": "2023-10-10 20:09:29",\n'
        '  "current": {\n'
        '    "url": "https://example.com",\n'
        '    "request_url": "https://example.com",\n'
        '    "request_fingerprint": "6d748741a927b10454c83ac285b002cd239964ea",\n'
        '    "page_type": null,\n'
        '    "probability": null\n'
        "  },\n"
        '  "to_crawl": {\n'
        '    "product": [],\n'
        '    "nextPage": [],\n'
        '    "subCategories": [],\n'
        '    "productNavigation": [],\n'
        '    "productNavigation-heuristics": [],\n'
        '    "unknown": []\n'
        "  }\n"
        "}"
    )


@freeze_time("2023-10-10 20:09:29")
def test_crawling_logs_middleware():
    middleware = CrawlingLogsMiddleware()

    url = "https://example.com"
    request = Request(url)
    response = Response(url=url, request=request)

    def results_gen():
        # product
        yield Request(
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

        # nextPage
        yield Request(
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

        # subCategories
        yield Request(
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

        # productNavigation
        yield Request(
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

        # productNavigation-heuristics
        yield Request(
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

        # unknown
        yield Request(
            "https://example.com/other-unknown",
            meta={
                "crawling_logs": {
                    "name": "Unknown Page",
                    "page_type": "some other page_type",
                },
            },
        )

    crawl_logs = middleware.crawl_logs(response, results_gen())
    assert crawl_logs == (
        "Crawling Logs for https://example.com (parsed as: None):\n"
        "Number of Requests per page type:\n"
        "- product: 1\n"
        "- nextPage: 1\n"
        "- subCategories: 1\n"
        "- productNavigation: 1\n"
        "- productNavigation-heuristics: 1\n"
        "- unknown: 1\n"
        "Structured Logs:\n"
        "{\n"
        '  "time": "2023-10-10 20:09:29",\n'
        '  "current": {\n'
        '    "url": "https://example.com",\n'
        '    "request_url": "https://example.com",\n'
        '    "request_fingerprint": "6d748741a927b10454c83ac285b002cd239964ea",\n'
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
        '        "request_fingerprint": "3ae14329c7fd5796ab543d7b02cdb7c7c2af3895"\n'
        "      }\n"
        "    ],\n"
        '    "nextPage": [\n'
        "      {\n"
        '        "name": "Category Page 2",\n'
        '        "probability": 0.9712,\n'
        '        "page_type": "nextPage",\n'
        '        "request_url": "https://example.com?page=2",\n'
        '        "request_priority": 100,\n'
        '        "request_fingerprint": "cf9e7c91564b16c204cdfa8fe3b4d7cb49375a2a"\n'
        "      }\n"
        "    ],\n"
        '    "subCategories": [\n'
        "      {\n"
        '        "name": "Monitors Subcategory",\n'
        '        "probability": 0.9817,\n'
        '        "page_type": "subCategories",\n'
        '        "request_url": "https://example.com/tech/products/monitors",\n'
        '        "request_priority": 98,\n'
        '        "request_fingerprint": "107253243fb9bc9c679808c6c5d80bde5ae7ffe0"\n'
        "      }\n"
        "    ],\n"
        '    "productNavigation": [\n'
        "      {\n"
        '        "name": "Books Category",\n'
        '        "probability": 0.9136,\n'
        '        "page_type": "productNavigation",\n'
        '        "request_url": "https://example.com/books/products",\n'
        '        "request_priority": 91,\n'
        '        "request_fingerprint": "e672605f85de9b9fe76e55463e5bd8ca66ae1ee2"\n'
        "      }\n"
        "    ],\n"
        '    "productNavigation-heuristics": [\n'
        "      {\n"
        '        "name": "Some Other Page",\n'
        '        "probability": 0.1,\n'
        '        "page_type": "productNavigation-heuristics",\n'
        '        "request_url": "https://example.com/some-other-page",\n'
        '        "request_priority": 10,\n'
        '        "request_fingerprint": "a04e46e1d9887a9f397d97c40db63a7ce3c3f958"\n'
        "      }\n"
        "    ],\n"
        '    "unknown": [\n'
        "      {\n"
        '        "name": "Unknown Page",\n'
        '        "page_type": "some other page_type",\n'
        '        "request_url": "https://example.com/other-unknown",\n'
        '        "request_priority": 0,\n'
        '        "request_fingerprint": "61fb82880551b45981b0a1cc52eb802166b673ed"\n'
        "      }\n"
        "    ]\n"
        "  }\n"
        "}"
    )


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
