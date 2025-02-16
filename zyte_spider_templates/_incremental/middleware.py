import logging
from typing import AsyncGenerator, Union

from scrapinghub.client.exceptions import Unauthorized
from scrapy.crawler import Crawler
from scrapy.exceptions import CloseSpider, NotConfigured
from scrapy.http import Request
from zyte_common_items import Item

from .manager import CollectionsFingerprintsManager, IncrementalCrawlingManager

logger = logging.getLogger(__name__)


class IncrementalCrawlMiddleware:
    """:ref:`Downloader middleware <topics-spider-middleware>` to skip
    items seen in previous crawls.

    To enable this middleware, set the :setting:`INCREMENTAL_CRAWL_ENABLED`
    setting to ``True``.

    This middleware keeps a record of URLs of crawled items in the :ref:`Zyte Scrapy Cloud
    collection <api-collections>` specified in the :setting:`INCREMENTAL_CRAWL_COLLECTION_NAME`
    setting, and skips items, responses and requests with matching URLs.

    Use :setting:`INCREMENTAL_CRAWL_BATCH_SIZE` to fine-tune interactions with
    the collection for performance.
    """

    def __init__(self, crawler: Crawler):
        assert crawler.spider
        if not crawler.spider.settings.getbool("INCREMENTAL_CRAWL_ENABLED", False):
            raise NotConfigured
        self.inc_manager: IncrementalCrawlingManager = self.prepare_incremental_manager(
            crawler
        )

    @staticmethod
    def prepare_incremental_manager(crawler):
        try:
            collection_fp = CollectionsFingerprintsManager(crawler)
        except (AttributeError, Unauthorized, RuntimeError, ValueError) as exc_info:
            logger.error(
                f"IncrementalCrawlMiddleware is enabled, but something went wrong with Collections.\n"
                f"The reason: {exc_info}"
            )
            raise CloseSpider("incremental_crawling_middleware_collection_issue")

        return IncrementalCrawlingManager(crawler, collection_fp)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        return cls(crawler)

    async def process_spider_output(
        self, response, result, spider
    ) -> AsyncGenerator[Union[Request, Item], None]:
        result_list = []
        async for item_or_request in result:
            result_list.append(item_or_request)

        unique_items_or_requests = await self.inc_manager.process_incremental_async(
            response.request, result_list
        )

        for item_or_request in unique_items_or_requests:
            yield item_or_request
