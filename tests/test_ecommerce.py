import logging
import re
from unittest.mock import MagicMock, call

import pytest
import scrapy
from pydantic import ValidationError
from scrapy_poet import DummyResponse
from scrapy_spider_metadata import get_spider_metadata
from zyte_common_items import ProbabilityRequest, Product, ProductNavigation, Request

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
from .test_utils import URL_TO_DOMAIN


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
    crawler = get_crawler()
    url = "https://example.com"
    spider = EcommerceSpider.from_crawler(crawler, url=url)
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
    assert len(requests) == 2
    urls = {request.url for request in requests}
    assert urls == {*subcategory_urls}
    assert all(request.callback == spider.parse_navigation for request in requests)
    assert [request.priority for request in requests] == [95, 78]

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
    assert len(requests) == 0

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
    "probability,has_item,item_drop",
    ((0.9, True, False), (0.09, False, True), (0.1, True, False), (None, True, False)),
)
def test_parse_product(probability, has_item, item_drop, caplog):
    caplog.clear()

    product_url = "https://example.com/product?id=123"
    product = Product.from_dict(
        {"url": product_url, "metadata": {"probability": probability}}
    )
    response = DummyResponse(product_url)
    spider = EcommerceSpider(url="https://example.com")
    mock_crawler = MagicMock()
    spider.crawler = mock_crawler
    logging.getLogger().setLevel(logging.INFO)
    items = list(spider.parse_product(response, product))
    if item_drop:
        assert mock_crawler.method_calls == [
            call.stats.inc_value("drop_item/product/low_probability")
        ]

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
        (
            "extract_from",
            "browserHtml",
            "ZYTE_API_PROVIDER_PARAMS",
            None,
            "getdict",
            {
                "productOptions": {"extractFrom": "browserHtml"},
                "productNavigationOptions": {"extractFrom": "browserHtml"},
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
                    "default": "full",
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
                            "description": (
                                "Follow pagination, subcategories, and "
                                "product detail pages. Pagination Only is a "
                                "better choice if the target URL does not "
                                "have subcategories, or if Zyte API is "
                                "misidentifying some URLs as subcategories."
                            ),
                            "title": "Navigation",
                        },
                        "pagination_only": {
                            "description": (
                                "Follow pagination and product detail pages. Subcategory links are ignored."
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
                    "description": (
                        "Initial URL for the crawl. Enter the full URL including http(s), "
                        "you can copy and paste it from your browser. Example: https://toscrape.com/"
                    ),
                    "pattern": r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$",
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


def test_get_subcategory_request():
    url = "https://example.com"

    # Normal request but with mostly empty values
    request = Request(url)
    spider = EcommerceSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore

    scrapy_request = spider.get_subcategory_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 0
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "",
            "probability": None,
            "page_type": "subCategories",
        },
    }

    # Non-Heuristics request
    request = ProbabilityRequest.from_dict(
        {"url": url, "name": "Some request", "metadata": {"probability": 0.98}}
    )
    spider = EcommerceSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore
    page_params = {"full_domain": "example.com"}

    scrapy_request = spider.get_subcategory_request(request, page_params=page_params)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 98
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "Some request",
            "probability": 0.98,
            "page_type": "subCategories",
        },
    }

    # Heuristics request
    request = ProbabilityRequest.from_dict(
        {
            "url": url,
            "name": "[heuristics] Some request",
            "metadata": {"probability": 0.1},
        }
    )
    spider = EcommerceSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore
    page_params = {"full_domain": "example.com"}

    scrapy_request = spider.get_subcategory_request(request, page_params=page_params)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 10
    assert scrapy_request.meta == {
        "page_params": page_params,
        "crawling_logs": {
            "name": "Some request",
            "probability": 0.1,
            "page_type": "productNavigation-heuristics",
        },
    }


def test_get_nextpage_request():
    url = "https://example.com"

    # Minimal Args
    request = Request(url)
    spider = EcommerceSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore

    scrapy_request = spider.get_nextpage_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 100
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {"name": "", "probability": None, "page_type": "nextPage"},
    }


def test_get_parse_navigation_request():
    url = "https://example.com"

    # Minimal args
    request = Request(url)
    spider = EcommerceSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore

    scrapy_request = spider.get_parse_navigation_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 0
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "",
            "probability": None,
            "page_type": "productNavigation",
        },
    }


@pytest.mark.parametrize("url,allowed_domain", URL_TO_DOMAIN)
def test_set_allowed_domains(url, allowed_domain):
    crawler = get_crawler()

    kwargs = {"url": url}
    spider = EcommerceSpider.from_crawler(crawler, **kwargs)
    assert spider.allowed_domains == [allowed_domain]
