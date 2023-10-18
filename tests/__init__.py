from typing import Any, Dict, Optional

from scrapy.utils.test import TestSpider


# scrapy.utils.test.get_crawler alternative that does not freeze settings.
def get_crawler(*, settings: Optional[Dict[str, Any]] = None):
    from scrapy.crawler import CrawlerRunner

    settings = settings or {}
    # Set by default settings that prevent deprecation warnings.
    settings["REQUEST_FINGERPRINTER_IMPLEMENTATION"] = "2.7"
    runner = CrawlerRunner(settings)
    crawler = runner.create_crawler(TestSpider)
    return crawler
