from importlib.metadata import version
from typing import Any, Dict

import scrapy
from pydantic import BaseModel, ConfigDict, model_validator
from scrapy.crawler import Crawler

from ..params import (
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    SeedUrlParam,
    UrlParam,
    UrlsParam,
)

# Higher priority than command-line-defined settings (40).
ARG_SETTING_PRIORITY: int = 50

_INPUT_FIELDS = ("url", "urls", "seed_url")


class BaseSpiderParams(
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    SeedUrlParam,
    UrlsParam,
    UrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        json_schema_extra={
            "groups": [
                {
                    "id": "inputs",
                    "title": "Inputs",
                    "description": (
                        "Input data that determines the start URLs of the crawl."
                    ),
                    "widget": "exclusive",
                },
            ],
        },
    )

    @model_validator(mode="after")
    def single_input(self):
        """Fields
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.url`
        and
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.seed_url`
        form a mandatory, mutually-exclusive field group: one of them must be
        defined, the rest must not be defined."""
        input_fields = set(
            field for field in _INPUT_FIELDS if getattr(self, field, None)
        )
        if not input_fields:
            input_field_list = ", ".join(_INPUT_FIELDS)
            raise ValueError(
                f"No input parameter defined. Please, define one of: "
                f"{input_field_list}."
            )
        elif len(input_fields) > 1:
            input_field_list = ", ".join(
                f"{field} ({getattr(self, field)!r})" for field in input_fields
            )
            raise ValueError(
                f"Expected a single input parameter, got {len(input_fields)}: "
                f"{input_field_list}."
            )
        return self


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
