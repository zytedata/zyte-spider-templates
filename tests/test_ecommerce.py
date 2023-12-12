import logging
import re

import pytest
import scrapy
from pydantic import ValidationError
from scrapy_poet import DummyResponse
from scrapy_spider_metadata import get_spider_metadata
from zyte_common_items import ProbabilityRequest, Product, ProductNavigation

from zyte_spider_templates import BaseSpiderParams
from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS,
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.spiders.ecommerce import (
    EcommerceCrawlStrategy,
    EcommerceSpider,
)

from . import get_crawler


def test_parameters():
    with pytest.raises(ValidationError):
        EcommerceSpider()

    EcommerceSpider(url="https://example.com")
    EcommerceSpider(
        url="https://example.com", crawl_strategy=EcommerceCrawlStrategy.full
    )
    EcommerceSpider(url="https://example.com", crawl_strategy="full")

    with pytest.raises(ValidationError):
        EcommerceSpider(url="https://example.com", crawl_strategy="unknown")


def test_start_requests():
    url = "https://example.com"
    spider = EcommerceSpider(url=url)
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == url
    assert requests[0].callback == spider.parse_navigation


def test_crawl():
    subcategory_urls = [
        "https://example.com/category/tech",
        "https://example.com/category/books",
    ]
    nextpage_url = "https://example.com/category/tech?p=2"
    item_urls = [
        "https://example.com/product?id=123",
        "https://example.com/product?id=988",
    ]
    request = scrapy.Request("https://example.com")
    response = DummyResponse(url=subcategory_urls[0], request=request)

    subcategories = {
        "subCategories": [
            {"url": subcategory_urls[0], "metadata": {"probability": 0.95}},
            {"url": subcategory_urls[1], "metadata": {"probability": 0.78}},
        ],
    }
    nextpage = {"nextPage": {"url": nextpage_url}}
    items = {
        "items": [
            {"url": item_urls[0], "metadata": {"probability": 0.99}},
            {"url": item_urls[1], "metadata": {"probability": 0.83}},
        ],
    }

    url = subcategory_urls[0]
    spider = EcommerceSpider(url="https://example.com/")

    # no links found
    navigation = ProductNavigation.from_dict({"url": url})
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 0

    # subcategories only
    navigation = ProductNavigation.from_dict({"url": url, **subcategories})
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 2
    assert requests[0].url == subcategory_urls[0]
    assert requests[0].callback == spider.parse_navigation
    assert requests[0].priority == 95
    assert requests[1].url == subcategory_urls[1]
    assert requests[1].callback == spider.parse_navigation
    assert requests[1].priority == 78

    # subcategories + nextpage
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **subcategories,
            **nextpage,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 3
    urls = {request.url for request in requests}
    assert urls == {*subcategory_urls, nextpage_url}
    assert all(request.callback == spider.parse_navigation for request in requests)
    assert [request.priority for request in requests] == [100, 95, 78]

    # subcategories + nextpage + items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **subcategories,
            **nextpage,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    urls = {request.url for request in requests}
    assert urls == {*item_urls, *subcategory_urls, nextpage_url}
    for request in requests:
        if request.url in item_urls:
            assert request.callback == spider.parse_product
        else:
            assert request.callback == spider.parse_navigation
    assert [request.priority for request in requests] == [199, 183, 100, 95, 78]

    # nextpage + items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **nextpage,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 3
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_product
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_product
    assert requests[2].url == nextpage_url
    assert requests[2].callback == spider.parse_navigation
    assert [request.priority for request in requests] == [199, 183, 100]

    # subcategories + items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **subcategories,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 4
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_product
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_product
    assert requests[2].url == subcategory_urls[0]
    assert requests[2].callback == spider.parse_navigation
    assert requests[3].url == subcategory_urls[1]
    assert requests[3].callback == spider.parse_navigation
    assert [request.priority for request in requests] == [199, 183, 95, 78]

    # nextpage
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **nextpage,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 1
    assert requests[0].url == nextpage_url
    assert requests[0].callback == spider.parse_navigation
    assert [request.priority for request in requests] == [100]

    # items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 2
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_product
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_product
    assert [request.priority for request in requests] == [199, 183]

    # Test parse_navigation() behavior on pagination_only crawl strategy.
    spider = EcommerceSpider(
        url="https://example.com/", crawl_strategy="pagination_only"
    )

    # nextpage + items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **subcategories,
            **nextpage,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    urls = {request.url for request in requests}
    assert urls == {*item_urls, nextpage_url}
    for request in requests:
        if request.url in item_urls:
            assert request.callback == spider.parse_product
        else:
            assert request.callback == spider.parse_navigation


@pytest.mark.parametrize(
    "probability,has_item", ((0.9, True), (0.09, False), (0.1, True), (None, True))
)
def test_parse_product(probability, has_item, caplog):
    caplog.clear()

    product_url = "https://example.com/product?id=123"
    product = Product.from_dict(
        {"url": product_url, "metadata": {"probability": probability}}
    )
    response = DummyResponse(product_url)
    spider = EcommerceSpider(url="https://example.com")
    logging.getLogger().setLevel(logging.INFO)
    items = list(spider.parse_product(response, product))

    if has_item:
        assert len(items) == 1
        assert items[0] == product
        assert caplog.text == ""
    else:
        assert len(items) == 0
        assert str(product) in caplog.text


def test_arguments():
    # Ensure passing no arguments works.
    crawler = get_crawler()

    # Needed since it's a required argument.
    base_kwargs = {"url": "https://example.com"}

    EcommerceSpider.from_crawler(crawler, **base_kwargs)

    for param, arg, setting, old_setting_value, getter_name, new_setting_value in (
        ("max_requests", "123", "ZYTE_API_MAX_REQUESTS", None, "getint", 123),
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
    ):
        kwargs = {param: arg}
        settings = {}
        if old_setting_value is not None:
            settings[setting] = old_setting_value
        crawler = get_crawler(settings=settings)
        spider = EcommerceSpider.from_crawler(crawler, **kwargs, **base_kwargs)
        getter = getattr(crawler.settings, getter_name)
        assert getter(setting) == new_setting_value
        assert spider.allowed_domains == ["example.com"]


def test_metadata():
    metadata = get_spider_metadata(EcommerceSpider, normalize=True)
    assert metadata == {
        "template": True,
        "title": "E-commerce",
        "description": "Template for spiders that extract product data from e-commerce websites.",
        "param_schema": {
            "properties": {
                "crawl_strategy": {
                    "default": "navigation",
                    "title": "Crawl strategy",
                    "description": "Determines how the start URL and follow-up URLs are crawled.",
                    "type": "string",
                    "enum": ["full", "navigation", "pagination_only"],
                    "enumMeta": {
                        "full": {
                            "description": "Follow most links within the domain of URL in an attempt to discover and extract as many products as possible.",
                            "title": "Full",
                        },
                        "navigation": {
                            "description": "Follow pagination, subcategories, and product detail pages.",
                            "title": "Navigation",
                        },
                        "pagination_only": {
                            "description": (
                                "Follow pagination and product detail pages. SubCategory links are ignored. "
                                "Use this when some subCategory links are misidentified by ML-extraction."
                            ),
                            "title": "Pagination Only",
                        },
                    },
                },
                "extract_from": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "title": "Extraction source",
                    "description": (
                        "Whether to perform extraction using a browser request "
                        "(browserHtml) or an HTTP request (httpResponseBody)."
                    ),
                    "enum": ["httpResponseBody", "browserHtml"],
                    "enumMeta": {
                        "httpResponseBody": {
                            "title": "httpResponseBody",
                            "description": "Use HTTP responses. Cost-efficient and fast extraction method, which works well on many websites.",
                        },
                        "browserHtml": {
                            "title": "browserHtml",
                            "description": "Use browser rendering. Often provides the best quality.",
                        },
                    },
                },
                "geolocation": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "title": "Geolocation",
                    "description": "ISO 3166-1 alpha-2 2-character string specified in "
                    "https://docs.zyte.com/zyte-api/usage/reference.html#operation/extract/request/geolocation.",
                    "enum": list(
                        sorted(GEOLOCATION_OPTIONS, key=GEOLOCATION_OPTIONS.__getitem__)
                    ),
                    "enumMeta": {
                        code: {
                            "title": GEOLOCATION_OPTIONS_WITH_CODE[code],
                        }
                        for code in Geolocation
                    },
                },
                "max_requests": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": 100,
                    "title": "Max Requests",
                    "description": (
                        "The maximum number of Zyte API requests allowed for the crawl.\n"
                        "\n"
                        "Requests with error responses that cannot be retried or exceed "
                        "their retry limit also count here, but they incur in no costs "
                        "and do not increase the request count in Scrapy Cloud."
                    ),
                    "widget": "request-limit",
                },
                "url": {
                    "type": "string",
                    "title": "URL",
                    "description": "Initial URL for the crawl.",
                    "pattern": r"^https?:\/\/[^:\/\s]+(:\d{1,5})?(\/[^\s]*)*(#[^\s]*)?$",
                },
            },
            "required": ["url"],
            "title": "EcommerceSpiderParams",
            "type": "object",
        },
    }
    geolocation = metadata["param_schema"]["properties"]["geolocation"]
    assert geolocation["enum"][0] == "AF"
    assert geolocation["enumMeta"]["UY"] == {"title": "Uruguay (UY)"}
    assert set(geolocation["enum"]) == set(geolocation["enumMeta"])


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
def test_validation_url(url, valid):
    url_re = BaseSpiderParams.model_fields["url"].metadata[0].pattern
    assert bool(re.match(url_re, url)) == valid


def test_get_parse_product_request():
    base_kwargs = {
        "url": "https://example.com",
    }
    crawler = get_crawler()

    # Crawls products outside of domains by default
    spider = EcommerceSpider.from_crawler(crawler, **base_kwargs)
    request = ProbabilityRequest(url="https://example.com")
    scrapy_request = spider.get_parse_product_request(request)
    assert scrapy_request.meta.get("allow_offsite") is True
