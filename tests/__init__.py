from importlib.metadata import version
from typing import Any, Dict, Optional, Type

import pytest
from packaging.version import Version
from scrapy import Spider

# https://docs.pytest.org/en/stable/how-to/writing_plugins.html#assertion-rewriting
pytest.register_assert_rewrite("tests.utils")


class _TestSpider(Spider):
    name = "test"


# scrapy.utils.test.get_crawler alternative that does not freeze settings.
def get_crawler(
    *, settings: Optional[Dict[str, Any]] = None, spider_cls: Type[Spider] = _TestSpider
):
    from scrapy.crawler import CrawlerRunner

    settings = settings or {}
    if Version(version("scrapy")) < Version("2.12"):
        # Prevent a deprecation warning about the default value.
        settings["REQUEST_FINGERPRINTER_IMPLEMENTATION"] = "2.7"
    runner = CrawlerRunner(settings)
    crawler = runner.create_crawler(spider_cls)
    return crawler
