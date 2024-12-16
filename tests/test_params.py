import re

import pytest
from pydantic import ValidationError

from zyte_spider_templates import EcommerceSpider, GoogleSearchSpider
from zyte_spider_templates.params import URL_FIELD_KWARGS
from zyte_spider_templates.spiders.ecommerce import EcommerceCrawlStrategy

from . import get_crawler


@pytest.mark.parametrize(
    "valid,url",
    [
        (False, ""),
        (False, "http://"),
        (False, "http:/example.com"),
        (False, "ftp://example.com"),
        (False, "example.com"),
        (False, "//example.com"),
        (False, "http://foo:bar@example.com"),
        (False, " http://example.com"),
        (False, "http://example.com "),
        (False, "http://examp le.com"),
        (False, "https://example.com:232323"),
        (True, "http://example.com"),
        (True, "http://bücher.example"),
        (True, "http://xn--bcher-kva.example"),
        (True, "https://i❤.ws"),
        (True, "https://example.com"),
        (True, "https://example.com/"),
        (True, "https://example.com:2323"),
        (True, "https://example.com:2323/"),
        (True, "https://example.com:2323/foo"),
        (True, "https://example.com/f"),
        (True, "https://example.com/foo"),
        (True, "https://example.com/foo/"),
        (True, "https://example.com/foo/bar"),
        (True, "https://example.com/foo/bar/"),
        (True, "https://example.com/foo/bar?baz"),
        (True, "https://example.com/foo/bar/?baz"),
        (True, "https://example.com?foo"),
        (True, "https://example.com?foo=bar"),
        (True, "https://example.com/?foo=bar&baz"),
        (True, "https://example.com/?foo=bar&baz#"),
        (True, "https://example.com/?foo=bar&baz#frag"),
        (True, "https://example.com#"),
        (True, "https://example.com/#"),
        (True, "https://example.com/&"),
        (True, "https://example.com/&#"),
    ],
)
def test_url_pattern(url, valid):
    assert isinstance(URL_FIELD_KWARGS["pattern"], str)
    assert bool(re.match(URL_FIELD_KWARGS["pattern"], url)) == valid


REQUIRED_ARGS = {
    EcommerceSpider: {"url": "https://example.com"},
    GoogleSearchSpider: {"search_queries": "foo"},
}


@pytest.mark.parametrize(
    ("spider_cls",), ((spider_cls,) for spider_cls in REQUIRED_ARGS)
)
def test_required_args(spider_cls):
    crawler = get_crawler()

    with pytest.raises(ValidationError):
        spider_cls.from_crawler(crawler)

    spider_cls.from_crawler(crawler, **REQUIRED_ARGS[spider_cls])


@pytest.mark.parametrize(
    ("spider_cls", "args", "valid"),
    (
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "crawl_strategy": EcommerceCrawlStrategy.automatic,
            },
            True,
        ),
        (
            EcommerceSpider,
            {"url": "https://example.com", "crawl_strategy": "automatic"},
            True,
        ),
        (
            EcommerceSpider,
            {"url": "https://example.com", "crawl_strategy": "unknown"},
            False,
        ),
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "crawl_strategy": "direct_item",
                "search_queries": "",
            },
            True,
        ),
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "crawl_strategy": "automatic",
                "search_queries": "foo",
            },
            True,
        ),
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "crawl_strategy": "direct_item",
                "search_queries": "foo",
            },
            False,
        ),
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "extract": "product",
                "crawl_strategy": "direct_item",
                "search_queries": "foo",
            },
            False,
        ),
        (
            EcommerceSpider,
            {
                "url": "https://example.com",
                "extract": "productList",
                "crawl_strategy": "direct_item",
                "search_queries": "foo",
            },
            True,
        ),
        (GoogleSearchSpider, {"domain": "google.com"}, False),
        (
            GoogleSearchSpider,
            {"domain": "google.cat", "search_queries": "foo bar"},
            True,
        ),
        (
            GoogleSearchSpider,
            {"domain": "google.cat", "search_queries": "foo bar", "max_pages": 10},
            True,
        ),
        (
            GoogleSearchSpider,
            {"domain": "google.foo", "search_queries": "foo bar"},
            False,
        ),
        (GoogleSearchSpider, {"search_queries": "foo bar", "max_pages": "all"}, False),
        (GoogleSearchSpider, {"search_queries": "foo", "results_per_page": 0}, False),
    ),
)
def test_arg_combinations(spider_cls, args, valid):
    crawler = get_crawler()
    if valid:
        spider_cls.from_crawler(crawler, **args)
    else:
        with pytest.raises(ValidationError):
            spider_cls.from_crawler(crawler, **args)


@pytest.mark.parametrize(
    ("spider_cls", "param", "arg", "setting", "old", "getter", "new"),
    (
        # extract_from
        *(
            (EcommerceSpider, *scenario)
            for scenario in (
                (
                    "extract_from",
                    "browserHtml",
                    "ZYTE_API_PROVIDER_PARAMS",
                    None,
                    "getdict",
                    {
                        "productOptions": {"extractFrom": "browserHtml"},
                        "productNavigationOptions": {"extractFrom": "browserHtml"},
                        "productListOptions": {"extractFrom": "browserHtml"},
                    },
                ),
                (
                    "extract_from",
                    "httpResponseBody",
                    "ZYTE_API_PROVIDER_PARAMS",
                    {"geolocation": "US"},
                    "getdict",
                    {
                        "productOptions": {"extractFrom": "httpResponseBody"},
                        "productNavigationOptions": {"extractFrom": "httpResponseBody"},
                        "productListOptions": {"extractFrom": "httpResponseBody"},
                        "geolocation": "US",
                    },
                ),
                (
                    "extract_from",
                    None,
                    "ZYTE_API_PROVIDER_PARAMS",
                    {"geolocation": "US"},
                    "getdict",
                    {"geolocation": "US"},
                ),
            )
        ),
        # geolocation
        *(
            (spider_cls, *scenario)
            for spider_cls in (EcommerceSpider, GoogleSearchSpider)
            for scenario in (
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_AUTOMAP_PARAMS",
                    None,
                    "getdict",
                    {"geolocation": "DE"},
                ),
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_AUTOMAP_PARAMS",
                    '{"browserHtml": true}',
                    "getdict",
                    {"browserHtml": True, "geolocation": "DE"},
                ),
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_AUTOMAP_PARAMS",
                    '{"geolocation": "IE"}',
                    "getdict",
                    {"geolocation": "DE"},
                ),
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_PROVIDER_PARAMS",
                    None,
                    "getdict",
                    {"geolocation": "DE"},
                ),
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_PROVIDER_PARAMS",
                    '{"browserHtml": true}',
                    "getdict",
                    {"browserHtml": True, "geolocation": "DE"},
                ),
                (
                    "geolocation",
                    "DE",
                    "ZYTE_API_PROVIDER_PARAMS",
                    '{"geolocation": "IE"}',
                    "getdict",
                    {"geolocation": "DE"},
                ),
            )
        ),
        # max_requests
        *(
            (
                spider_cls,
                "max_requests",
                "123",
                "ZYTE_API_MAX_REQUESTS",
                None,
                "getint",
                123,
            )
            for spider_cls in (EcommerceSpider, GoogleSearchSpider)
        ),
    ),
)
def test_setting_setter_params(spider_cls, param, arg, setting, old, getter, new):
    settings = {}
    if old is not None:
        settings[setting] = old
    crawler = get_crawler(settings=settings)
    spider_cls.from_crawler(crawler, **REQUIRED_ARGS[spider_cls], **{param: arg})
    read = getattr(crawler.settings, getter)
    assert read(setting) == new
