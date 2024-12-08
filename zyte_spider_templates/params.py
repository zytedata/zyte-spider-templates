import json
import re
from enum import Enum
from logging import getLogger
from typing import Any, Dict, List, Optional, Union

import requests
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    Json,
    NonNegativeInt,
    field_validator,
    model_validator,
)

try:
    from pydantic.config import JsonDict
except ImportError:
    JsonValue = Union[int, float, str, bool, None, List["JsonValue"], "JsonDict"]
    JsonDict = Dict[str, JsonValue]  # type: ignore[misc]

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.documentation import document_enum

from .utils import _URL_PATTERN, get_domain, load_url_list

logger = getLogger(__name__)


@document_enum
class ExtractFrom(str, Enum):
    httpResponseBody: str = "httpResponseBody"
    """Use raw responses. Fast and cheap."""

    browserHtml: str = "browserHtml"
    """Use browser rendering. Better quality, but slower and more expensive."""


@document_enum
class CustomAttrsMethod(str, Enum):
    generate: str = "generate"
    """Use a generative model (LLM). The most powerful and versatile, but more
    expensive, with variable per-request cost."""

    extract: str = "extract"
    """Use an extractive model (BERT). Supports only a subset of the schema (string,
    integer and number), suited for extraction of short and clear fields, with a fixed
    per-request cost."""


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
                    "description": "Use browser rendering. Better quality, but slower and more expensive.",
                },
                ExtractFrom.httpResponseBody: {
                    "title": "httpResponseBody",
                    "description": "Use raw responses. Fast and cheap.",
                },
            },
        },
    )


class GeolocationParam(BaseModel):
    geolocation: Optional[Geolocation] = Field(
        title="Geolocation",
        description="Country of the IP addresses to use.",
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


class SearchQueriesParam(BaseModel):
    search_queries: List[str] = Field(
        title="Search Queries",
        description=(
            "A list of search queries, one per line, to submit using the "
            "search form found on each input URL."
        ),
        default_factory=list,
        json_schema_extra={
            "default": [],
            "widget": "textarea",
        },
    )

    @field_validator("search_queries", mode="before")
    @classmethod
    def validate_search_queries(cls, value: Union[List[str], str]) -> List[str]:
        """Validate a list of search queries.

        If a string is received as input, it is split into multiple strings
        on new lines.
        """
        if isinstance(value, str):
            value = value.split("\n")
        if not value:
            return value
        result = []
        for v in value:
            if not (v := v.strip()):
                continue
            result.append(v)
        return result


INPUT_GROUP_FIELDS = ("url", "urls", "urls_file")
INPUT_GROUP: JsonDict = {
    "id": "inputs",
    "title": "Inputs",
    "description": "Input data that determines the start URLs of the crawl.",
    "widget": "exclusive",
}


def validate_input_group(model):
    input_fields = set(
        field for field in INPUT_GROUP_FIELDS if getattr(model, field, None)
    )
    if not input_fields:
        input_field_list = ", ".join(INPUT_GROUP_FIELDS)
        raise ValueError(
            f"No input parameter defined. Please, define one of: "
            f"{input_field_list}."
        )
    elif len(input_fields) > 1:
        input_field_list = ", ".join(
            f"{field} ({getattr(model, field)!r})" for field in input_fields
        )
        raise ValueError(
            f"Expected a single input parameter, got {len(input_fields)}: "
            f"{input_field_list}."
        )
    return model


URLS_FILE_FIELD_KWARGS = {
    "title": "URLs file",
    "description": (
        "URL that point to a plain-text file with a list of URLs to "
        "crawl, e.g. https://example.com/url-list.txt. The linked file "
        "must contain 1 URL per line."
    ),
    "pattern": _URL_PATTERN,
    "default": "",
    "json_schema_extra": {
        "group": "inputs",
        "exclusiveRequired": True,
    },
}


class UrlsFileParam(BaseModel):
    urls_file: str = Field(**URLS_FILE_FIELD_KWARGS)  # type: ignore[call-overload, misc, arg-type]

    @model_validator(mode="after")
    def input_group(self):
        return validate_input_group(self)


def parse_input_params(spider):
    urls_file = spider.args.urls_file
    if urls_file:
        response = requests.get(urls_file)
        urls = load_url_list(response.text)
        spider.logger.info(f"Loaded {len(urls)} initial URLs from {urls_file}.")
        spider.start_urls = urls
    elif spider.args.urls:
        spider.start_urls = spider.args.urls
    else:
        spider.start_urls = [spider.args.url]
    spider.allowed_domains = list(set(get_domain(url) for url in spider.start_urls))


URL_FIELD_KWARGS = {
    "title": "URL",
    "description": (
        "Initial URL for the crawl. Enter the full URL including http(s), "
        "you can copy and paste it from your browser. Example: "
        "https://toscrape.com/"
    ),
    "pattern": _URL_PATTERN,
    "default": "",
    "json_schema_extra": {
        "group": "inputs",
        "exclusiveRequired": True,
    },
}


class UrlParam(BaseModel):
    url: str = Field(**URL_FIELD_KWARGS)  # type: ignore[call-overload, misc, arg-type]


URLS_FIELD_KWARGS = {
    "title": "URLs",
    "description": (
        "Initial URLs for the crawl, separated by new lines. Enter the "
        "full URL including http(s), you can copy and paste it from your "
        "browser. Example: https://toscrape.com/"
    ),
    "default": None,
    "json_schema_extra": {
        "group": "inputs",
        "exclusiveRequired": True,
        "widget": "textarea",
    },
}


def validate_url_list(value: Union[List[str], str]) -> List[str]:
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

    @model_validator(mode="after")
    def input_group(self):
        return validate_input_group(self)


class UrlsParam(BaseModel):
    urls: Optional[List[str]] = Field(**URLS_FIELD_KWARGS)  # type: ignore[call-overload, misc, arg-type]

    @model_validator(mode="after")
    def input_group(self):
        return validate_input_group(self)

    @field_validator("urls", mode="before")
    @classmethod
    def validate_url_list(cls, value: Union[List[str], str]) -> List[str]:
        return validate_url_list(value)


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
        cls, value: Optional[Union[PostalAddress, str, Dict]]
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


class CustomAttrsInputParam(BaseModel):
    custom_attrs_input: Optional[Json[Dict[str, Any]]] = Field(
        title="Custom attributes schema",
        description="Custom attributes to extract.",
        default=None,
        json_schema_extra={
            "widget": "custom-attrs",
        },
    )


class CustomAttrsMethodParam(BaseModel):
    custom_attrs_method: CustomAttrsMethod = Field(
        title="Custom attributes extraction method",
        description="Which model to use for custom attribute extraction.",
        default=CustomAttrsMethod.generate,
        json_schema_extra={
            "enumMeta": {
                CustomAttrsMethod.generate: {
                    "title": "generate",
                    "description": "Use a generative model (LLM). The most powerful "
                    "and versatile, but more expensive, with variable "
                    "per-request cost.",
                },
                CustomAttrsMethod.extract: {
                    "title": "extract",
                    "description": "Use an extractive model (BERT). Supports only a "
                    "subset of the schema (string, integer and "
                    "number), suited for extraction of short and clear "
                    "fields, with a fixed per-request cost.",
                },
            },
        },
    )


class MaxRequestsPerSeedParam(BaseModel):
    max_requests_per_seed: Optional[NonNegativeInt] = Field(
        title="Max requests per seed",
        description=(
            "The maximum number of follow-up requests allowed per initial URL. "
            "Unlimited if not set."
        ),
        default=None,
    )
