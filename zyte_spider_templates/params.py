import re
from enum import Enum
from logging import getLogger
from typing import List, Optional, Union

from pydantic import BaseModel, Field, field_validator

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.documentation import document_enum

from .utils import _URL_PATTERN

logger = getLogger(__name__)


@document_enum
class ExtractFrom(str, Enum):
    httpResponseBody: str = "httpResponseBody"
    """Use HTTP responses. Cost-efficient and fast extraction method, which
    works well on many websites."""

    browserHtml: str = "browserHtml"
    """Use browser rendering. Often provides the best quality."""


class ExtractFromParam(BaseModel):
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


class GeolocationParam(BaseModel):
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


class MaxRequestsParam(BaseModel):
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


class SeedUrlParam(BaseModel):
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


class UrlParam(BaseModel):
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


class UrlsParam(BaseModel):
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
        if not value:
            return value
        result = []
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
            result.append(v)
        if not result:
            raise ValueError(f"No valid URL found in {value!r}")
        return result
