import pytest
import scrapy
from duplicate_url_discarder_rules import RULE_PATHS
from packaging import version
from scrapy.utils.test import get_crawler

from zyte_spider_templates import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
    IncrementalCrawlMiddleware,
    MaxRequestsPerSeedDownloaderMiddleware,
    OffsiteRequestsPerSeedMiddleware,
    OnlyFeedsMiddleware,
    TrackNavigationDepthSpiderMiddleware,
    TrackSeedsSpiderMiddleware,
)

_crawler = get_crawler()
BASELINE_SETTINGS = _crawler.settings.copy_to_dict()

try:
    from scrapy.downloadermiddlewares.offsite import OffsiteMiddleware  # noqa: F401
except ImportError:
    BUILTIN_OFFSITE_MIDDLEWARE_IMPORT_PATH = (
        "scrapy.spidermiddlewares.offsite.OffsiteMiddleware"
    )
else:
    BUILTIN_OFFSITE_MIDDLEWARE_IMPORT_PATH = (
        "scrapy.downloadermiddlewares.offsite.OffsiteMiddleware"
    )


# https://github.com/scrapy-plugins/scrapy-zyte-api/blob/a1d81d11854b420248f38e7db49c685a8d46d943/tests/test_addon.py#L109
def _test_setting_changes(initial_settings, expected_settings):
    settings = {
        **initial_settings,
        "ADDONS": {
            "zyte_spider_templates.Addon": 1000,
        },
    }
    crawler = get_crawler(settings_dict=settings)
    crawler._apply_settings()
    actual_settings = crawler.settings.copy_to_dict()

    # Test separately settings that copy_to_dict messes up.
    for setting in (
        "DOWNLOADER_MIDDLEWARES",
        "SCRAPY_POET_PROVIDERS",
        "SPIDER_MIDDLEWARES",
    ):
        if setting not in crawler.settings:
            assert setting not in expected_settings
            continue
        assert crawler.settings.getdict(setting) == expected_settings.pop(setting)
        del actual_settings[setting]

    for key in BASELINE_SETTINGS:
        if key in actual_settings and actual_settings[key] == BASELINE_SETTINGS[key]:
            del actual_settings[key]
    del actual_settings["ADDONS"]

    assert actual_settings == expected_settings


@pytest.mark.parametrize(
    ("initial_settings", "expected_settings"),
    (
        (
            {},
            {
                "CLOSESPIDER_TIMEOUT_NO_ITEM": 600,
                "DOWNLOADER_MIDDLEWARES": {
                    MaxRequestsPerSeedDownloaderMiddleware: 100,
                    BUILTIN_OFFSITE_MIDDLEWARE_IMPORT_PATH: None,
                    AllowOffsiteMiddleware: 50,
                },
                "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
                "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
                "SCHEDULER_PRIORITY_QUEUE": "scrapy.pqueues.DownloaderAwarePriorityQueue",
                "ITEM_PROBABILITY_THRESHOLDS": {
                    "zyte_common_items.items.Article": 0.1,
                    "zyte_common_items.items.Product": 0.1,
                },
                "DUD_LOAD_RULE_PATHS": RULE_PATHS,
                "SCRAPY_POET_DISCOVER": [
                    "zyte_spider_templates.pages",
                ],
                "SPIDER_MIDDLEWARES": {
                    IncrementalCrawlMiddleware: 45,
                    OffsiteRequestsPerSeedMiddleware: 49,
                    OnlyFeedsMiddleware: 108,
                    TrackNavigationDepthSpiderMiddleware: 110,
                    TrackSeedsSpiderMiddleware: 550,
                    CrawlingLogsMiddleware: 1000,
                },
                "SPIDER_MODULES": [
                    "zyte_spider_templates.spiders",
                ],
            },
        ),
    ),
)
@pytest.mark.skipif(
    version.parse(scrapy.__version__) < version.parse("2.11.2"),
    reason="Test applicable only for Scrapy versions >= 2.11.2",
)
def test_poet_setting_changes_since_scrapy_2_11_2(initial_settings, expected_settings):
    _test_setting_changes(initial_settings, expected_settings)


@pytest.mark.parametrize(
    ("initial_settings", "expected_settings"),
    (
        (
            {},
            {
                "CLOSESPIDER_TIMEOUT_NO_ITEM": 600,
                "DOWNLOADER_MIDDLEWARES": {MaxRequestsPerSeedDownloaderMiddleware: 100},
                "SCHEDULER_DISK_QUEUE": "scrapy.squeues.PickleFifoDiskQueue",
                "SCHEDULER_MEMORY_QUEUE": "scrapy.squeues.FifoMemoryQueue",
                "SCHEDULER_PRIORITY_QUEUE": "scrapy.pqueues.DownloaderAwarePriorityQueue",
                "ITEM_PROBABILITY_THRESHOLDS": {
                    "zyte_common_items.items.Article": 0.1,
                    "zyte_common_items.items.Product": 0.1,
                },
                "DUD_LOAD_RULE_PATHS": RULE_PATHS,
                "SCRAPY_POET_DISCOVER": [
                    "zyte_spider_templates.pages",
                ],
                "SPIDER_MIDDLEWARES": {
                    IncrementalCrawlMiddleware: 45,
                    OffsiteRequestsPerSeedMiddleware: 49,
                    OnlyFeedsMiddleware: 108,
                    TrackNavigationDepthSpiderMiddleware: 110,
                    BUILTIN_OFFSITE_MIDDLEWARE_IMPORT_PATH: None,
                    AllowOffsiteMiddleware: 500,
                    TrackSeedsSpiderMiddleware: 550,
                    CrawlingLogsMiddleware: 1000,
                },
                "SPIDER_MODULES": [
                    "zyte_spider_templates.spiders",
                ],
            },
        ),
    ),
)
@pytest.mark.skipif(
    version.parse(scrapy.__version__) >= version.parse("2.11.2"),
    reason="Test applicable only for Scrapy versions < 2.11.2",
)
def test_poet_setting_changes(initial_settings, expected_settings):
    _test_setting_changes(initial_settings, expected_settings)
