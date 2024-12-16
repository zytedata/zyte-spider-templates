from unittest.mock import patch

import pytest
from scrapy.exceptions import CloseSpider, NotConfigured
from scrapy.http import Request, Response
from scrapy.settings import Settings
from scrapy.statscollectors import StatsCollector
from scrapy.utils.request import RequestFingerprinter

from tests import get_crawler
from zyte_spider_templates import IncrementalCrawlMiddleware
from zyte_spider_templates._incremental.manager import IncrementalCrawlingManager
from zyte_spider_templates.spiders.article import ArticleSpider


def crawler_for_incremental():
    url = "https://example.com"
    crawler = get_crawler()
    crawler.request_fingerprinter = RequestFingerprinter()
    crawler.stats = StatsCollector(crawler)
    crawler.spider = ArticleSpider.from_crawler(crawler, url=url)
    crawler.settings["ZYTE_PROJECT_ID"] = "000000"
    return crawler


def test_middleware_init_not_configured():
    crawler = crawler_for_incremental()
    crawler.spider.settings = Settings({"INCREMENTAL_CRAWL_ENABLED": False})

    with pytest.raises(NotConfigured) as exc_info:
        IncrementalCrawlMiddleware(crawler)
    assert str(exc_info.value) == (
        "IncrementalCrawlMiddleware is not enabled. Set the "
        "INCREMENTAL_CRAWL_ENABLED setting to True to enable it."
    )


@patch("scrapinghub.ScrapinghubClient")
def test_middleware_init_configured(mock_scrapinghub_client):
    crawler = crawler_for_incremental()
    crawler.spider.settings = Settings({"INCREMENTAL_CRAWL_ENABLED": True})

    middleware = IncrementalCrawlMiddleware(crawler)
    assert isinstance(middleware.inc_manager, IncrementalCrawlingManager)


@patch("scrapinghub.ScrapinghubClient")
def test_prepare_manager_with_collection_fp_success(mock_scrapinghub_client):
    crawler = crawler_for_incremental()
    crawler.spider.settings = Settings({"INCREMENTAL_CRAWL_ENABLED": True})

    manager = IncrementalCrawlMiddleware.prepare_incremental_manager(crawler)
    assert isinstance(manager, IncrementalCrawlingManager)


def test_prepare_manager_with_collection_fp_failure(caplog):
    crawler = crawler_for_incremental()
    crawler.spider.settings = Settings({"INCREMENTAL_CRAWL_ENABLED": True})

    caplog.clear()
    with pytest.raises(CloseSpider) as exc_info:
        IncrementalCrawlMiddleware.prepare_incremental_manager(crawler)
    assert exc_info.value.reason == "incremental_crawling_middleware_collection_issue"
    assert caplog.messages[-1].startswith(
        "IncrementalCrawlMiddleware is enabled, but something went wrong with Collections."
    )


@patch("scrapinghub.ScrapinghubClient")
@pytest.mark.asyncio
async def test_middleware_process_spider_output(mock_scrapinghub_client):
    crawler = crawler_for_incremental()
    crawler.spider.settings = Settings({"INCREMENTAL_CRAWL_ENABLED": True})

    middleware = IncrementalCrawlMiddleware(crawler)
    request = Request(url=crawler.spider.url)
    response = Response(url=crawler.spider.url, request=request)
    input_result = [
        Request(url="https://example.com/1"),
        Request(url="https://example.com/2"),
        Request(url="https://example.com/3"),
    ]

    async def async_generator():
        for item in input_result:
            yield item

    processed_result_list = []

    async for processed_item in middleware.process_spider_output(
        response, async_generator(), crawler.spider
    ):
        processed_result_list.append(processed_item)

    for res_ex, res_proc in zip(input_result, processed_result_list):
        assert res_ex == res_proc
