from importlib.metadata import version
from typing import Any, Dict
from warnings import warn

import scrapy
from pydantic import BaseModel, ConfigDict, model_validator
from scrapy.crawler import Crawler

from ..params import (
    INPUT_GROUP,
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    UrlParam,
    UrlsFileParam,
    UrlsParam,
)

# Higher priority than command-line-defined settings (40).
ARG_SETTING_PRIORITY: int = 50


class BaseSpiderParams(
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    UrlsFileParam,
    UrlsParam,
    UrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        json_schema_extra={
            "groups": [
                INPUT_GROUP,
            ],
        },
    )

    @model_validator(mode="after")
    def deprecated(self):
        warn(
            (
                "BaseSpiderParams is deprecated, use pydantic.BaseModel and "
                "your desired combination of classes from "
                "zyte_spider_templates.params instead."
            ),
            DeprecationWarning,
        )


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

        if geolocation := getattr(spider.args, "geolocation", None):
            # We set the geolocation in ZYTE_API_PROVIDER_PARAMS for injected
            # dependencies, and in ZYTE_API_AUTOMAP_PARAMS for page object
            # additional requests.
            for component in ("AUTOMAP", "PROVIDER"):
                default_params = spider.settings.getdict(f"ZYTE_API_{component}_PARAMS")
                default_params["geolocation"] = geolocation
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
