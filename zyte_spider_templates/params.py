from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.documentation import document_enum


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


class UrlParam(BaseModel):
    url: str = Field(
        title="URL",
        description="Initial URL for the crawl. Enter the full URL including http(s), "
        "you can copy and paste it from your browser. Example: https://toscrape.com/",
        pattern=r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$",
    )
