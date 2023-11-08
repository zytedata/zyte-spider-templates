import json
import logging
import warnings
from datetime import datetime
from typing import Any, Dict

from scrapy import Request
from scrapy.exceptions import CloseSpider, ScrapyDeprecationWarning
from scrapy.utils.request import request_fingerprint
from zyte_api.aio.errors import RequestError

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

    valid_page_types = [
        "product",
        "nextPage",
        "subCategories",
        "productNavigation",
        "productNavigation-heuristics",
    ]
    unknown_page_type = "unknown"

    def process_spider_output(self, response, result, spider):
        result = list(result)
        crawl_logs = self.crawl_logs(response, result)
        logger.info(crawl_logs)
        return result

    def crawl_logs(self, response, result):
        current_page_type = response.meta.get("crawling_logs", {}).get("page_type")
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore",
                category=ScrapyDeprecationWarning,
                message="Call to deprecated function scrapy.utils.request.request_fingerprint()*",
            )
            fingerprint = request_fingerprint(response.request)
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
            "to_crawl": {},
        }

        for page_type in self.valid_page_types + [self.unknown_page_type]:
            data["to_crawl"][page_type] = []

        if result:
            for entry in result:
                if not isinstance(entry, Request):
                    continue

                crawling_logs = entry.meta.get("crawling_logs", {})
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        category=ScrapyDeprecationWarning,
                        message="Call to deprecated function scrapy.utils.request.request_fingerprint()*",
                    )
                    entry_fingerprint = request_fingerprint(entry)
                crawling_logs.update(
                    {
                        "request_url": entry.url,
                        "request_priority": entry.priority,
                        "request_fingerprint": entry_fingerprint,
                    }
                )

                page_type = crawling_logs.get("page_type")
                if page_type not in self.valid_page_types:
                    page_type = self.unknown_page_type

                data["to_crawl"][page_type].append(crawling_logs)

        summary = ["Number of Requests per page type:"]
        for page_type, requests in data["to_crawl"].items():
            summary.append(f"- {page_type}: {len(requests)}")

        report = [
            f"Crawling Logs for {response.url} (parsed as: {current_page_type}):",
            "\n".join(summary),
            "Structured Logs:",
            json.dumps(data, indent=2),
        ]
        return "\n".join(report)


start_requests_processed = object()


class ForbiddenDomainSpiderMiddleware:
    """Marks start requests and reports to
    :class:`ForbiddenDomainDownloaderMiddleware` the number of them once all
    have been processed."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self._send_signal = crawler.signals.send_catch_log

    def process_start_requests(self, start_requests, spider):
        count = 0
        for request in start_requests:
            request.meta["is_start_request"] = True
            yield request
            count += 1
        self._send_signal(start_requests_processed, count=count)


class ForbiddenDomainDownloaderMiddleware:
    """Closes the spider with ``failed-forbidden-domain`` as close reason if
    all start requests get a 451 response from Zyte API."""

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self._failed_start_request_count = 0
        self._total_start_request_count = 0
        crawler.signals.connect(
            self.start_requests_processed, signal=start_requests_processed
        )

    def start_requests_processed(self, count):
        self._total_start_request_count = count
        self.maybe_close()  # TODO: Ensure that raising here works.

    def process_exception(self, request, exception, spider):
        if (
            not request.meta.get("is_start_request")
            or not isinstance(exception, RequestError)
            or exception.status != 451
        ):
            return

        self._failed_start_request_count += 1

        if not self._total_start_request_count:
            return
        else:
            self.maybe_close()  # TODO: Ensure that raising here works.

    def maybe_close(self):
        if self._failed_start_request_count >= self._total_start_request_count:
            logger.error(
                "Stopping the spider, all start request failed because they "
                "were pointing to a domain forbidden by Zyte API."
            )
            raise CloseSpider("failed-forbidden-domain")
