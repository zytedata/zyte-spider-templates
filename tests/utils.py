from __future__ import annotations

import json
from typing import Any

from aiohttp.test_utils import TestServer
from scrapy import Spider, signals
from scrapy.utils.defer import deferred_to_future

from . import get_crawler


def assertEqualSpiderMetadata(actual, expected):
    """Compare 2 JSON schemas of spider metadata.

    The parameter order in the parameter schema is taken into account, given
    how it affects the UI, while the order of other object keys may be
    different.

    It also generates a better diff in pytest output when enums are involved,
    e.g. geolocation values.
    """
    assert tuple(actual["param_schema"]["properties"]) == tuple(
        expected["param_schema"]["properties"]
    )
    actual_json = json.dumps(actual, indent=2, sort_keys=True)
    expected_json = json.dumps(expected, indent=2, sort_keys=True)
    assert actual_json == expected_json


def get_addons() -> dict[str | type, int]:
    addons: dict[str | type, int] = {
        "scrapy_zyte_api.Addon": 500,
        "zyte_spider_templates.Addon": 1000,
    }
    try:
        from scrapy_poet import Addon
    except ImportError:
        pass
    else:
        addons[Addon] = 300
    return addons


def get_zyte_api_settings(zyte_api_server) -> dict[str, Any]:
    return {
        "ZYTE_API_URL": str(zyte_api_server.make_url("/")),
        "ZYTE_API_KEY": "a",
        "ADDONS": get_addons(),
    }


async def crawl_fake_zyte_api(
    zyte_api_server: TestServer,
    spider_cls: type[Spider],
    spider_kwargs: dict[str, Any],
    settings: dict[str, Any] | None = None,
):
    settings = {**get_zyte_api_settings(zyte_api_server), **(settings or {})}
    crawler = get_crawler(settings=settings, spider_cls=spider_cls)
    items = []

    def track_item(item, response, spider):
        items.append(item)

    crawler.signals.connect(track_item, signal=signals.item_scraped)
    await deferred_to_future(crawler.crawl(**spider_kwargs))
    return items
