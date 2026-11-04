from unittest.mock import patch

import pytest
from pytest_twisted import ensureDeferred
from scrapy import Request
from scrapy.statscollectors import StatsCollector
from scrapy.utils.request import RequestFingerprinter
from zyte_common_items import Article

from tests import get_crawler
from zyte_spider_templates import ArticleSpider
from zyte_spider_templates._incremental.manager import (
    CollectionsFingerprintsManager,
    IncrementalCrawlingManager,
)


def crawler_for_incremental():
    url = "https://example.com"
    crawler = get_crawler()
    crawler.settings["REQUEST_FINGERPRINTER_IMPLEMENTATION"] = "2.7"
    crawler.request_fingerprinter = RequestFingerprinter(crawler)
    crawler.stats = StatsCollector(crawler)
    crawler.spider = ArticleSpider.from_crawler(crawler, url=url)
    crawler.settings["ZYTE_PROJECT_ID"] = "000000"
    return crawler


@patch("scrapinghub.ScrapinghubClient")
@pytest.mark.parametrize(
    "input_request, input_result, expected_result, duplicated_fingerprints_result, expected_stats",
    [
        (
            Request(url="https://example.com/article.html"),
            [],
            [],
            set(),
            {"incremental_crawling/filtered_items_and_requests": 0},
        ),  # no results
        (
            Request(url="https://example.com/article.html"),
            [Article(url="https://example.com/article.html")],
            [Article(url="https://example.com/article.html")],
            set(),
            {
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 1,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item in the result without redirected URL
        (
            Request(url="https://example.com/article.html"),
            [Article(url="https://example.com/article1.html")],
            [Article(url="https://example.com/article1.html")],
            set(),
            {
                "incremental_crawling/redirected_urls": 1,
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 2,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item with redirected URL in the result
        (
            Request(url="https://example.com/article.html"),
            [
                Article(
                    url="https://example.com/article1.html",
                    canonicalUrl="https://example.com/article1.html",
                )
            ],
            [Article(url="https://example.com/article1.html")],
            set(),
            {
                "incremental_crawling/redirected_urls": 1,
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 2,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item with redirected URL and the same canonicalURL in the result
        (
            Request(url="https://example.com/article.html"),
            [
                Article(
                    url="https://example.com/article1.html",
                    canonicalUrl="https://example.com/article2.html",
                )
            ],
            [Article(url="https://example.com/article1.html")],
            set(),
            {
                "incremental_crawling/redirected_urls": 1,
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 3,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item with redirected URL and the different canonicalURL in the result
        (
            Request(url="https://example.com/article.html"),
            [
                Article(
                    url="https://example.com/article.html",
                    canonicalUrl="https://example.com/article1.html",
                )
            ],
            [Article(url="https://example.com/article.html")],
            set(),
            {
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 2,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item with only canonicalURL different in the result
        (
            Request(url="https://example.com/article.html"),
            [
                Article(
                    url="https://example.com/article.html",
                    canonicalUrl="https://example.com/article.html",
                )
            ],
            [Article(url="https://example.com/article.html")],
            set(),
            {
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/fingerprint_url_to_batch": 1,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Only one Item with all equal URLS in the result
        (
            Request(url="https://example.com/list.html"),
            [Request(url="https://example.com/article1.html")],
            [Request(url="https://example.com/article1.html")],
            set(),
            {
                "incremental_crawling/filtered_items_and_requests": 0,
                "incremental_crawling/requests_to_check": 1,
            },
        ),  # Only one Request in the result, no Items, no existing fingerprints in the cache
        (
            Request(url="https://example.com/list.html"),
            [
                Request(url="https://example.com/article1.html"),
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
            ],
            [
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
            ],
            {
                (
                    "c300aee49364a341855bb1b08fa010497d4220016642",
                    "https://example.com/article1.html",
                )
            },
            {
                "incremental_crawling/filtered_items_and_requests": 1,
                "incremental_crawling/requests_to_check": 3,
            },
        ),  # Three Requests in the result, no Items, one existing fingerprint in the cache
        (
            Request(url="https://example.com/list.html"),
            [
                Request(url="https://example.com/article1.html"),
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
            ],
            [
                Request(url="https://example.com/article2.html"),
            ],
            {
                (
                    "c300aee49364a341855bb1b08fa010497d4220016642",
                    "https://example.com/article1.html",
                ),
                (
                    "c3001e046b02318004f724350aa3c9d3c6693a0ee4a9",
                    "https://example.com/article3.html",
                ),
            },
            {
                "incremental_crawling/filtered_items_and_requests": 2,
                "incremental_crawling/requests_to_check": 3,
            },
        ),  # Three Requests in the result, no Items, two existing fingerprints in the cache
        (
            Request(url="https://example.com/list.html"),
            [
                Request(url="https://example.com/article1.html"),
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
            ],
            [],
            {
                (
                    "c300aee49364a341855bb1b08fa010497d4220016642",
                    "https://example.com/article1.html",
                ),
                (
                    "c3001e046b02318004f724350aa3c9d3c6693a0ee4a9",
                    "https://example.com/article3.html",
                ),
                (
                    "c30004342f6c6f4a8f25c2d615f524af1fe266894be8",
                    "https://example.com/article2.html",
                ),
            },
            {
                "incremental_crawling/filtered_items_and_requests": 3,
                "incremental_crawling/requests_to_check": 3,
            },
        ),  # Three Requests in the result, no Items, three existing fingerprints in the cache
        (
            Request(url="https://example.com/article.html"),
            [
                Request(url="https://example.com/article1.html"),
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
                Article(url="https://example.com/article.html"),
            ],
            [
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
                Article(url="https://example.com/article.html"),
            ],
            {
                (
                    "c300aee49364a341855bb1b08fa010497d4220016642",
                    "https://example.com/article1.html",
                )
            },
            {
                "incremental_crawling/filtered_items_and_requests": 1,
                "incremental_crawling/requests_to_check": 3,
                "incremental_crawling/fingerprint_url_to_batch": 1,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Three Requests and one Item without redirected URL in the result, one existing fingerprint in the cache
        (
            Request(url="https://example.com/list.html"),
            [
                Request(url="https://example.com/article1.html"),
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
                Article(url="https://example.com/article.html"),
            ],
            [
                Request(url="https://example.com/article2.html"),
                Request(url="https://example.com/article3.html"),
                Article(url="https://example.com/article.html"),
            ],
            {
                (
                    "c300aee49364a341855bb1b08fa010497d4220016642",
                    "https://example.com/article1.html",
                )
            },
            {
                "incremental_crawling/redirected_urls": 1,
                "incremental_crawling/filtered_items_and_requests": 1,
                "incremental_crawling/requests_to_check": 3,
                "incremental_crawling/fingerprint_url_to_batch": 2,
                "incremental_crawling/add_to_batch": 1,
            },
        ),  # Three Requests and one Item with redirected URL in the result, one existing fingerprint in the cache
    ],
)
@ensureDeferred
async def test_process_incremental(
    mock_scrapinghub_client,
    input_request,
    input_result,
    expected_result,
    duplicated_fingerprints_result,
    expected_stats,
):
    crawler = crawler_for_incremental()
    fp_manager = CollectionsFingerprintsManager(crawler)
    manager = IncrementalCrawlingManager(crawler, fp_manager)
    fp_manager.batch = duplicated_fingerprints_result

    processed_result = await manager.process_incremental_async(
        input_request, input_result.copy()
    )
    assert len(expected_result) == len(processed_result)
    for expected, processed in zip(expected_result, processed_result):
        assert expected.url == processed.url  # type: ignore

    assert crawler.stats.get_stats() == expected_stats


@patch("scrapinghub.ScrapinghubClient")
@ensureDeferred
async def test_process_incremental_several_items(
    mock_scrapinghub_client,
):
    crawler = crawler_for_incremental()

    fp_manager = CollectionsFingerprintsManager(crawler)
    manager = IncrementalCrawlingManager(crawler, fp_manager)

    input_request = Request(url="https://example.com/article.html")
    input_result = [
        Request(url="https://example.com/article1.html"),
        Article(url="https://example.com/article.html"),
        Article(url="https://example.com/article.html"),
    ]
    with pytest.raises(NotImplementedError):
        await manager.process_incremental_async(input_request, input_result.copy())


@patch("scrapinghub.ScrapinghubClient")
@pytest.mark.parametrize(
    "request_url, item, expected",
    [
        (
            "https://example.com/article.html",
            Article(url="https://example.com/article.html"),
            {"https://example.com/article.html": "request_url"},
        ),
        (
            "https://example.com/article.html",
            Article(url="https://example.com/article1.html"),
            {
                "https://example.com/article.html": "request_url",
                "https://example.com/article1.html": "url",
            },
        ),
        (
            "https://example.com/article.html",
            Article(
                url="https://example.com/article.html",
                canonicalUrl="https://example.com/article.html",
            ),
            {"https://example.com/article.html": "request_url"},
        ),
        (
            "https://example.com/article.html",
            Article(
                url="https://example.com/article1.html",
                canonicalUrl="https://example.com/article1.html",
            ),
            {
                "https://example.com/article.html": "request_url",
                "https://example.com/article1.html": "url",
            },
        ),
        (
            "https://example.com/article.html",
            Article(
                url="https://example.com/article1.html",
                canonicalUrl="https://example.com/article2.html",
            ),
            {
                "https://example.com/article.html": "request_url",
                "https://example.com/article1.html": "url",
                "https://example.com/article2.html": "canonicalUrl",
            },
        ),
    ],
)
def test_get_unique_urls(mock_scrapinghub_client, request_url, item, expected):
    crawler = crawler_for_incremental()

    fp_manager = CollectionsFingerprintsManager(crawler)
    manager = IncrementalCrawlingManager(crawler, fp_manager)
    assert manager._get_unique_urls(request_url, item) == expected
