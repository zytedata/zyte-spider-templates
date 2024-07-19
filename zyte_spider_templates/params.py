import json
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, Field, ConfigDict, field_validator

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

class PostalAddress(BaseModel):
    """
    Represents a postal address with various optional components such as
    street address, postal code, region, and country.
    """

    model_config = ConfigDict(extra="forbid")

    streetAddress: Optional[str] = Field(
        title="Street Address",
        description="The street address",
        default=None,
    )

    postalCode: Optional[str] = Field(
        title="Postal Code",
        description="The postal code",
        default=None,
    )

    addressRegion: Optional[str] = Field(
        title="Address Region",
        description="The region in which the address is. This value is specific to the website",
        default=None,
    )

    addressCountry: Optional[str] = Field(
        title="Adress Country",
        description="The country code in ISO 3166-1 alpha-2",
        default=None,
    )


class LocationParam(BaseModel):
    """
    Represents a parameter containing a postal address to be set as the user location on websites.
    """

    location: Optional[PostalAddress] = Field(
        title="Location",
        description="Postal address to be set as the user location on websites",
        default=None,
    )

    @field_validator("location", mode="before")
    @classmethod
    def validate_location(
        cls, value: Optional[Union[str, dict, PostalAddress]]
    ) -> Optional[PostalAddress]:
        """Validate location field and cast it into PostalAddress if needed"""
        if value is None or isinstance(value, PostalAddress):
            return value

        if isinstance(value, str):
            try:
                return PostalAddress(**json.loads(value))
            except json.decoder.JSONDecodeError as err:
                raise ValueError(f"{value!r} is not a valid JSON object") from err

        elif isinstance(value, dict):
            return PostalAddress(**value)

        raise ValueError(f"{value!r} type {type(value)} is not a supported type")
