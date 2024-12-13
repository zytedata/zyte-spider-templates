from __future__ import annotations

from importlib.metadata import version
from typing import TYPE_CHECKING, Annotated, Any, Dict
from warnings import warn

import scrapy
from pydantic import BaseModel, ConfigDict, model_validator
from scrapy.crawler import Crawler
from scrapy_zyte_api import custom_attrs
from zyte_common_items import CustomAttributes

from ..params import (
    INPUT_GROUP,
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    SearchQueriesParam,
    UrlParam,
    UrlsFileParam,
    UrlsParam,
)

if TYPE_CHECKING:
    # typing.Self requires Python 3.11
    from typing_extensions import Self


class _LogExceptionsContextManager:
    def __init__(self, spider, exc_info):
        self._spider = spider
        self._exc_info = exc_info

    def __enter__(self):
        return

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None:
            return True
        if issubclass(exc_type, self._exc_info):
            self._spider.logger.exception(exc_value)
            return True
        return False


# Higher priority than command-line-defined settings (40).
ARG_SETTING_PRIORITY: int = 50


class BaseSpiderParams(
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    SearchQueriesParam,
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
        return self


class BaseSpider(scrapy.Spider):
    custom_settings: Dict[str, Any] = {  # type: ignore[assignment]
        "ZYTE_API_TRANSPARENT_MODE": True,
        "_ZYTE_API_USER_AGENT": f"zyte-spider-templates/{version('zyte-spider-templates')}",
    }

    metadata: Dict[str, Any] = {
        "template": True,
        "title": "Base",
        "description": "Base template.",
    }

    _NEXT_PAGE_PRIORITY: int = 100

    _custom_attrs_dep = None
    _log_request_exception: _LogExceptionsContextManager = None  # type: ignore[assignment]

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)

        # all subclasses of this need to also have Args as a subclass
        # this may be possible to express in type hints instead
        assert hasattr(spider, "args")

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

        if custom_attrs_input := getattr(spider.args, "custom_attrs_input", None):
            custom_attrs_options = {
                "method": spider.args.custom_attrs_method,
            }
            if max_input_tokens := crawler.settings.getint("ZYTE_API_MAX_INPUT_TOKENS"):
                custom_attrs_options["maxInputTokens"] = max_input_tokens
            if max_output_tokens := crawler.settings.getint(
                "ZYTE_API_MAX_OUTPUT_TOKENS"
            ):
                custom_attrs_options["maxOutputTokens"] = max_output_tokens

            spider._custom_attrs_dep = Annotated[
                CustomAttributes,
                custom_attrs(custom_attrs_input, custom_attrs_options),
            ]

        spider._log_request_exception = _LogExceptionsContextManager(spider, ValueError)

        return spider
