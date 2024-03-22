from importlib.metadata import version
from typing import Any, Dict

import scrapy
from pydantic import BaseModel
from scrapy.crawler import Crawler

from ..params import ExtractFromParam, GeolocationParam, MaxRequestsParam, UrlParam

# Higher priority than command-line-defined settings (40).
ARG_SETTING_PRIORITY: int = 50


class BaseSpiderParams(
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    UrlParam,
    BaseModel,
):
    pass


class BaseSpider(scrapy.Spider):
    custom_settings: Dict[str, Any] = {
        "ZYTE_API_TRANSPARENT_MODE": True,
        "_ZYTE_API_USER_AGENT": f"zyte-spider-templates/{version('zyte-spider-templates')}",
    }

    metadata: Dict[str, Any] = {
        "template": True,
        "title": "Base",
        "description": "Base template.",
    }

    _NEXT_PAGE_PRIORITY: int = 100

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> scrapy.Spider:
        spider = super().from_crawler(crawler, *args, **kwargs)

        if spider.args.geolocation:
            # We set the geolocation in ZYTE_API_PROVIDER_PARAMS for injected
            # dependencies, and in ZYTE_API_AUTOMAP_PARAMS for page object
            # additional requests.
            for component in ("AUTOMAP", "PROVIDER"):
                default_params = spider.settings.getdict(f"ZYTE_API_{component}_PARAMS")
                default_params["geolocation"] = spider.args.geolocation
                spider.settings.set(
                    f"ZYTE_API_{component}_PARAMS",
                    default_params,
                    priority=ARG_SETTING_PRIORITY,
                )

        if spider.args.max_requests:
            spider.settings.set(
                "ZYTE_API_MAX_REQUESTS",
                spider.args.max_requests,
                priority=ARG_SETTING_PRIORITY,
            )
        return spider
