from typing import Any, Dict, Optional, Type

import pytest
from scrapy import Spider
from scrapy.utils.test import TestSpider

# https://docs.pytest.org/en/stable/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("tests.utils")


# scrapy.utils.test.get_crawler alternative that does not freeze settings.
def get_crawler(
    *, settings: Optional[Dict[str, Any]] = None, spider_cls: Type[Spider] = TestSpider
):
    from scrapy.crawler import CrawlerRunner

    settings = settings or {}
    # Set by default settings that prevent deprecation warnings.
    settings["REQUEST_FINGERPRINTER_IMPLEMENTATION"] = "2.7"
    runner = CrawlerRunner(settings)
    crawler = runner.create_crawler(spider_cls)
    return crawler
