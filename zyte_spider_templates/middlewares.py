import json
import logging
import warnings
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict
from warnings import warn

from scrapy import Request, Spider
from scrapy.spidermiddlewares.offsite import OffsiteMiddleware

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
    def _filter(self, request: Any, spider: Spider) -> bool:
        if not isinstance(request, Request):
            return True
        if request.meta.get("allow_offsite"):
            return True
        return super()._filter(request, spider)
