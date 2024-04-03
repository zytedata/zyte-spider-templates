import re
from enum import Enum
from importlib.metadata import version
from logging import getLogger
from typing import Any, Dict, List, Optional, Union

import scrapy
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from scrapy.crawler import Crawler

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.documentation import document_enum

# Higher priority than command-line-defined settings (40).
ARG_SETTING_PRIORITY: int = 50

logger = getLogger(__name__)


@document_enum
class ExtractFrom(str, Enum):
    httpResponseBody: str = "httpResponseBody"
    """Use HTTP responses. Cost-efficient and fast extraction method, which
    works well on many websites."""

    browserHtml: str = "browserHtml"
    """Use browser rendering. Often provides the best quality."""


_INPUT_FIELDS = ("url", "urls", "seed_url")
_URL_PATTERN = r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$"


class BaseSpiderParams(BaseModel):
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

    url: str = Field(
        title="URL",
        description="Initial URL for the crawl. Enter the full URL including http(s), "
        "you can copy and paste it from your browser. Example: https://toscrape.com/",
        pattern=_URL_PATTERN,
        default="",
        json_schema_extra={
            "group": "inputs",
            "exclusiveRequired": True,
        },
    )
    urls: Optional[List[str]] = Field(
        title="URLs",
        description=(
            "Initial URLs for the crawl, separated by new lines. Enter the "
            "full URL including http(s), you can copy and paste it from your "
            "browser. Example: https://toscrape.com/"
        ),
        default=None,
        json_schema_extra={
            "group": "inputs",
            "exclusiveRequired": True,
            "widget": "textarea",
        },
    )
    seed_url: str = Field(
        title="Seed URL",
        description=(
            "URL that point to a list of URLs to crawl, e.g. "
            "https://example.com/url-list.txt. The linked list must contain 1 "
            "URL per line."
        ),
        pattern=_URL_PATTERN,
        default="",
        json_schema_extra={
            "group": "inputs",
            "exclusiveRequired": True,
        },
    )
    geolocation: Optional[Geolocation] = Field(
        title="Geolocation",
        description="ISO 3166-1 alpha-2 2-character string specified in "
        "https://docs.zyte.com/zyte-api/usage/reference.html#operation/extract/request/geolocation.",
        default=None,
        json_schema_extra={
            "enumMeta": {
                code: {
                    "title": GEOLOCATION_OPTIONS_WITH_CODE[code],
                }
                for code in Geolocation
            }
        },
    )
    max_requests: Optional[int] = Field(
        description=(
            "The maximum number of Zyte API requests allowed for the crawl.\n"
            "\n"
            "Requests with error responses that cannot be retried or exceed "
            "their retry limit also count here, but they incur in no costs "
            "and do not increase the request count in Scrapy Cloud."
        ),
        default=100,
        json_schema_extra={
            "widget": "request-limit",
        },
    )
    extract_from: Optional[ExtractFrom] = Field(
        title="Extraction source",
        description=(
            "Whether to perform extraction using a browser request "
            "(browserHtml) or an HTTP request (httpResponseBody)."
        ),
        default=None,
        json_schema_extra={
            "enumMeta": {
                ExtractFrom.browserHtml: {
                    "title": "browserHtml",
                    "description": "Use browser rendering. Often provides the best quality.",
                },
                ExtractFrom.httpResponseBody: {
                    "title": "httpResponseBody",
                    "description": "Use HTTP responses. Cost-efficient and fast extraction method, which works well on many websites.",
                },
            },
        },
    )

    @field_validator("urls", mode="before")
    @classmethod
    def validate_url_list(cls, value: Union[List[str], str]) -> List[str]:
        """Validate a list of URLs.

        If a string is received as input, it is split into multiple strings
        on new lines.

        List items that do not match a URL pattern trigger a warning and are
        removed from the list. If all URLs are invalid, validation fails.
        """
        if isinstance(value, str):
            value = value.split("\n")
        if value:
            new_value = []
            for v in value:
                v = v.strip()
                if not v:
                    continue
                if not re.search(_URL_PATTERN, v):
                    logger.warning(
                        f"{v!r}, from the 'urls' spider argument, is not a "
                        f"valid URL and will be ignored."
                    )
                    continue
                new_value.append(v)
            if new_value:
                value = new_value
            else:
                raise ValueError(f"No valid URL found in {value!r}")
        return value

    @model_validator(mode="after")
    def single_input(self):
        """Fields
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.url`
        and
        :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.urls`
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
