import logging
from typing import Iterable, List, cast
from unittest.mock import MagicMock, call, patch

import pytest
import requests
import scrapy
from pytest_twisted import ensureDeferred
from scrapy import signals
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import get_spider_metadata
from web_poet.page_inputs.browser import BrowserResponse
from zyte_common_items import (
    ProbabilityRequest,
    Product,
    ProductNavigation,
    SearchRequestTemplate,
    SearchRequestTemplateMetadata,
)

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS,
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.spiders.ecommerce import EcommerceSpider

from . import get_crawler
from .test_utils import URL_TO_DOMAIN
from .utils import assertEqualSpiderMetadata


def test_start_requests():
    url = "https://example.com"
    crawler = get_crawler()
    spider = EcommerceSpider.from_crawler(crawler, url=url)
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == url
    assert requests[0].callback == spider.parse_navigation


def test_start_requests_crawling_logs_page_type():
    url = "https://example.com"
    crawler = get_crawler()

    spider = EcommerceSpider.from_crawler(crawler, url=url)
    requests = list(spider.start_requests())
    assert requests[0].meta["crawling_logs"]["page_type"] == "productNavigation"

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, crawl_strategy="direct_item"
    )
    requests = list(spider.start_requests())
    assert requests[0].meta["crawling_logs"]["page_type"] == "product"

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, extract="product", crawl_strategy="direct_item"
    )
    requests = list(spider.start_requests())
    assert requests[0].meta["crawling_logs"]["page_type"] == "product"

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, extract="productList", crawl_strategy="direct_item"
    )
    requests = list(spider.start_requests())
    assert requests[0].meta["crawling_logs"]["page_type"] == "productList"


def test_crawl():
    crawler = get_crawler()

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
    spider = EcommerceSpider.from_crawler(crawler, url="https://example.com/")

    def _get_requests(navigation: ProductNavigation) -> List[scrapy.Request]:
        return list(
            cast(
                Iterable[scrapy.Request],
                spider.parse_navigation(response, navigation, DynamicDeps()),
            )
        )

    # no links found
    navigation = ProductNavigation.from_dict({"url": url})
    requests = _get_requests(navigation)
    assert len(requests) == 0

    # subcategories only
    navigation = ProductNavigation.from_dict({"url": url, **subcategories})
    requests = _get_requests(navigation)
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
    requests = _get_requests(navigation)
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
    requests = _get_requests(navigation)
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
    requests = _get_requests(navigation)
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
    requests = _get_requests(navigation)
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
    requests = _get_requests(navigation)
    assert len(requests) == 0

    # items
    navigation = ProductNavigation.from_dict(
        {
            "url": url,
            **items,
        }
    )
    requests = _get_requests(navigation)
    assert len(requests) == 2
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_product
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_product
    assert [request.priority for request in requests] == [199, 183]

    # Test parse_navigation() behavior on pagination_only crawl strategy.
    spider = EcommerceSpider.from_crawler(
        crawler, url="https://example.com/", crawl_strategy="pagination_only"
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
    requests = _get_requests(navigation)
    urls = {request.url for request in requests}
    assert urls == {*item_urls, nextpage_url}
    for request in requests:
        if request.url in item_urls:
            assert request.callback == spider.parse_product
        else:
            assert request.callback == spider.parse_navigation


@pytest.mark.parametrize(
    ("args", "output"),
    (
        *(
            (
                {"url": "https://example.com/", **crawl_strategy_args, **extract_args},
                {
                    "https://example.com/product/1",
                    "https://example.com/product/2",
                    "https://example.com/page/2/product/1",
                    "https://example.com/page/2/product/2",
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                    "https://example.com/non-navigation/product/1",
                    "https://example.com/non-navigation/product/2",
                },
            )
            for crawl_strategy_args in ({}, {"crawl_strategy": "automatic"})
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    **crawl_strategy_args,
                    **extract_args,
                },
                {
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                },
            )
            for crawl_strategy_args in ({}, {"crawl_strategy": "automatic"})
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/",
                    "crawl_strategy": "full",
                    **extract_args,
                },
                {
                    "https://example.com/product/1",
                    "https://example.com/product/2",
                    "https://example.com/page/2/product/1",
                    "https://example.com/page/2/product/2",
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                    "https://example.com/non-navigation/product/1",
                    "https://example.com/non-navigation/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    "crawl_strategy": "full",
                    **extract_args,
                },
                {
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                    "https://example.com/non-navigation/product/1",
                    "https://example.com/non-navigation/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/",
                    "crawl_strategy": "navigation",
                    **extract_args,
                },
                {
                    "https://example.com/product/1",
                    "https://example.com/product/2",
                    "https://example.com/page/2/product/1",
                    "https://example.com/page/2/product/2",
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    "crawl_strategy": "navigation",
                    **extract_args,
                },
                {
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/",
                    "crawl_strategy": "pagination_only",
                    **extract_args,
                },
                {
                    "https://example.com/product/1",
                    "https://example.com/product/2",
                    "https://example.com/page/2/product/1",
                    "https://example.com/page/2/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    "crawl_strategy": "pagination_only",
                    **extract_args,
                },
                {
                    "https://example.com/category/1/product/1",
                    "https://example.com/category/1/product/2",
                    "https://example.com/category/1/page/2/product/1",
                    "https://example.com/category/1/page/2/product/2",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/",
                    "crawl_strategy": "direct_item",
                    **extract_args,
                },
                {
                    "https://example.com/",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    "crawl_strategy": "direct_item",
                    **extract_args,
                },
                {
                    "https://example.com/category/1",
                },
            )
            for extract_args in ({}, {"extract": "product"})
        ),
        *(
            (
                {
                    "url": "https://example.com/",
                    "extract": "productList",
                    **crawl_strategy_args,
                },
                {
                    "https://example.com/",
                    "https://example.com/page/2",
                    "https://example.com/category/1",
                    "https://example.com/category/1/page/2",
                    "https://example.com/non-navigation",
                },
            )
            for crawl_strategy_args in ({}, {"crawl_strategy": "automatic"})
        ),
        *(
            (
                {
                    "url": "https://example.com/category/1",
                    "extract": "productList",
                    **crawl_strategy_args,
                },
                {
                    "https://example.com/category/1",
                    "https://example.com/category/1/page/2",
                },
            )
            for crawl_strategy_args in ({}, {"crawl_strategy": "automatic"})
        ),
        (
            {
                "url": "https://example.com/",
                "crawl_strategy": "full",
                "extract": "productList",
            },
            {
                "https://example.com/",
                "https://example.com/page/2",
                "https://example.com/category/1",
                "https://example.com/category/1/page/2",
                "https://example.com/non-navigation",
            },
        ),
        (
            {
                "url": "https://example.com/category/1",
                "crawl_strategy": "full",
                "extract": "productList",
            },
            {
                "https://example.com/category/1",
                "https://example.com/category/1/page/2",
                "https://example.com/non-navigation",
            },
        ),
        (
            {
                "url": "https://example.com/",
                "crawl_strategy": "navigation",
                "extract": "productList",
            },
            {
                "https://example.com/",
                "https://example.com/page/2",
                "https://example.com/category/1",
                "https://example.com/category/1/page/2",
            },
        ),
        (
            {
                "url": "https://example.com/category/1",
                "crawl_strategy": "navigation",
                "extract": "productList",
            },
            {
                "https://example.com/category/1",
                "https://example.com/category/1/page/2",
            },
        ),
        (
            {
                "url": "https://example.com/",
                "crawl_strategy": "pagination_only",
                "extract": "productList",
            },
            {
                "https://example.com/",
                "https://example.com/page/2",
            },
        ),
        (
            {
                "url": "https://example.com/category/1",
                "crawl_strategy": "pagination_only",
                "extract": "productList",
            },
            {
                "https://example.com/category/1",
                "https://example.com/category/1/page/2",
            },
        ),
        (
            {
                "url": "https://example.com/",
                "crawl_strategy": "direct_item",
                "extract": "productList",
            },
            {
                "https://example.com/",
            },
        ),
        (
            {
                "url": "https://example.com/category/1",
                "crawl_strategy": "direct_item",
                "extract": "productList",
            },
            {
                "https://example.com/category/1",
            },
        ),
    ),
)
@ensureDeferred
async def test_crawl_strategies(args, output, mockserver):
    settings = {
        "ZYTE_API_URL": mockserver.urljoin("/"),
        "ZYTE_API_KEY": "a",
        "ADDONS": {"scrapy_zyte_api.Addon": 500},
    }
    crawler = get_crawler(settings=settings, spider_cls=EcommerceSpider)
    actual_output = set()

    def track_item(item, response, spider):
        actual_output.add(item.url)

    crawler.signals.connect(track_item, signal=signals.item_scraped)
    await crawler.crawl(**args)
    assert actual_output == output


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
    items = list(spider.parse_product(response, product, DynamicDeps()))
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


@pytest.mark.parametrize(
    ("probability", "yields_items"),
    (
        (None, True),  # Default
        (-1.0, False),
        (0.0, False),  # page.no_item_found()
        (1.0, True),
    ),
)
def test_parse_search_request_template_probability(probability, yields_items):
    crawler = get_crawler()
    spider = EcommerceSpider.from_crawler(
        crawler, url="https://example.com", search_queries="foo"
    )
    search_request_template = SearchRequestTemplate(url="https://example.com")
    if probability is not None:
        search_request_template.metadata = SearchRequestTemplateMetadata(
            probability=probability
        )
    items = list(
        spider.parse_search_request_template(
            DummyResponse("https://example.com"), search_request_template, DynamicDeps()
        )
    )
    assert items if yields_items else not items


def test_metadata():
    actual_metadata = get_spider_metadata(EcommerceSpider, normalize=True)
    expected_metadata = {
        "template": True,
        "title": "E-commerce",
        "description": "Template for spiders that extract product data from e-commerce websites.",
        "param_schema": {
            "groups": [
                {
                    "description": (
                        "Input data that determines the start URLs of the crawl."
                    ),
                    "id": "inputs",
                    "title": "Inputs",
                    "widget": "exclusive",
                },
            ],
            "properties": {
                "url": {
                    "default": "",
                    "description": (
                        "Initial URL for the crawl. Enter the full URL including http(s), "
                        "you can copy and paste it from your browser. Example: https://toscrape.com/"
                    ),
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "pattern": r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$",
                    "title": "URL",
                    "type": "string",
                },
                "urls": {
                    "anyOf": [
                        {"items": {"type": "string"}, "type": "array"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "Initial URLs for the crawl, separated by new lines. Enter the "
                        "full URL including http(s), you can copy and paste it from your "
                        "browser. Example: https://toscrape.com/"
                    ),
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "title": "URLs",
                    "widget": "textarea",
                },
                "urls_file": {
                    "default": "",
                    "description": (
                        "URL that point to a plain-text file with a list of "
                        "URLs to crawl, e.g. "
                        "https://example.com/url-list.txt. The linked file "
                        "must contain 1 URL per line."
                    ),
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "pattern": r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$",
                    "title": "URLs file",
                    "type": "string",
                },
                "search_queries": {
                    "default": [],
                    "description": (
                        "A list of search queries, one per line, to submit "
                        "using the search form found on each input URL. Only "
                        "works for input URLs that support search. May not "
                        "work on every website. Search queries are not "
                        'compatible with the "full" and "navigation" '
                        "crawl strategies, and when extracting products, they "
                        'are not compatible with the "direct_item" crawl '
                        "strategy either."
                    ),
                    "items": {"type": "string"},
                    "title": "Search Queries",
                    "type": "array",
                    "widget": "textarea",
                },
                "extract": {
                    "default": "product",
                    "description": "Data to return.",
                    "title": "Extract",
                    "enum": [
                        "product",
                        "productList",
                    ],
                    "type": "string",
                },
                "crawl_strategy": {
                    "default": "automatic",
                    "description": "Determines how the start URL and follow-up URLs are crawled.",
                    "enumMeta": {
                        "automatic": {
                            "description": (
                                "Automatically select the best approach. A good "
                                "default for most use cases. Currently it uses "
                                "heuristics only on the homepages of websites (similar "
                                "to Full strategy), and follows product, category and "
                                "pagination links on other pages (similar to Navigation "
                                "strategy)."
                            ),
                            "title": "Automatic",
                        },
                        "direct_item": {
                            "description": (
                                "Directly extract items from the provided "
                                "URLs, without any crawling. To use this "
                                "strategy, pass to the spider individual "
                                "product or product list URLs (in line with "
                                "the extract spider parameter value). Common "
                                "use cases are product monitoring and batch "
                                "extraction."
                            ),
                            "title": "Direct URLs",
                        },
                        "full": {
                            "description": (
                                "Follow most links on the website to discover and "
                                "extract as many products as possible. If an input URL "
                                "is a link to a particular category on a website, the "
                                "spider may crawl products outside this category. Try "
                                "this strategy if other strategies miss items."
                            ),
                            "title": "Full",
                        },
                        "navigation": {
                            "description": (
                                "Follow pagination, subcategories, and product links "
                                "only. If an input URL is a link to a particular "
                                "category on a website, the spider will try to stay "
                                "within this category."
                            ),
                            "title": "Navigation",
                        },
                        "pagination_only": {
                            "description": (
                                "Follow pagination and product links only. This "
                                "strategy is similar to Navigation, but it doesn't "
                                "support subcategories. Use it when you need the "
                                "spider to stay within a certain category on a "
                                "website, but Automatic or Navigation strategies fail "
                                "to do so because of misclassified subcategory links."
                            ),
                            "title": "Pagination Only",
                        },
                    },
                    "title": "Crawl strategy",
                    "enum": [
                        "automatic",
                        "full",
                        "navigation",
                        "pagination_only",
                        "direct_item",
                    ],
                    "type": "string",
                },
                "geolocation": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": "Country of the IP addresses to use.",
                    "enumMeta": {
                        code: {
                            "title": GEOLOCATION_OPTIONS_WITH_CODE[code],
                        }
                        for code in sorted(Geolocation)
                    },
                    "title": "Geolocation",
                    "enum": list(
                        sorted(GEOLOCATION_OPTIONS, key=GEOLOCATION_OPTIONS.__getitem__)
                    ),
                },
                "max_requests": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": 100,
                    "description": (
                        "The maximum number of Zyte API requests allowed for the crawl.\n"
                        "\n"
                        "Requests with error responses that cannot be retried or exceed "
                        "their retry limit also count here, but they incur in no costs "
                        "and do not increase the request count in Scrapy Cloud."
                    ),
                    "title": "Max Requests",
                    "widget": "request-limit",
                },
                "extract_from": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "default": None,
                    "description": (
                        "Whether to perform extraction using a browser request "
                        "(browserHtml) or an HTTP request (httpResponseBody)."
                    ),
                    "enumMeta": {
                        "browserHtml": {
                            "description": "Use browser rendering. Better quality, but slower and more expensive.",
                            "title": "browserHtml",
                        },
                        "httpResponseBody": {
                            "description": "Use raw responses. Fast and cheap.",
                            "title": "httpResponseBody",
                        },
                    },
                    "title": "Extraction source",
                    "enum": ["httpResponseBody", "browserHtml"],
                },
                "custom_attrs_input": {
                    "anyOf": [
                        {
                            "contentMediaType": "application/json",
                            "contentSchema": {"type": "object"},
                            "type": "string",
                        },
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": "Custom attributes to extract.",
                    "title": "Custom attributes schema",
                    "widget": "custom-attrs",
                },
                "custom_attrs_method": {
                    "default": "generate",
                    "description": "Which model to use for custom attribute extraction.",
                    "enum": ["generate", "extract"],
                    "enumMeta": {
                        "extract": {
                            "description": "Use an extractive model (BERT). Supports only a "
                            "subset of the schema (string, integer and "
                            "number), suited for extraction of short and clear "
                            "fields, with a fixed per-request cost.",
                            "title": "extract",
                        },
                        "generate": {
                            "description": "Use a generative model (LLM). The most powerful "
                            "and versatile, but more expensive, with variable "
                            "per-request cost.",
                            "title": "generate",
                        },
                    },
                    "title": "Custom attributes extraction method",
                    "type": "string",
                },
            },
            "title": "EcommerceSpiderParams",
            "type": "object",
        },
    }
    assertEqualSpiderMetadata(actual_metadata, expected_metadata)

    geolocation = actual_metadata["param_schema"]["properties"]["geolocation"]
    assert geolocation["enum"][0] == "AF"
    assert geolocation["enumMeta"]["UY"] == {"title": "Uruguay (UY)"}
    assert set(geolocation["enum"]) == set(geolocation["enumMeta"])


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
    request = ProbabilityRequest(url=url)
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
    request = ProbabilityRequest(url=url)
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
    request = ProbabilityRequest(url=url)
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
    assert spider.allowed_domains == [allowed_domain]  # type: ignore[attr-defined]


def test_input_none():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        EcommerceSpider.from_crawler(crawler)


def test_input_multiple():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        EcommerceSpider.from_crawler(
            crawler,
            url="https://a.example",
            urls=["https://b.example"],
        )
    with pytest.raises(ValueError):
        EcommerceSpider.from_crawler(
            crawler,
            url="https://a.example",
            urls_file="https://b.example",
        )
    with pytest.raises(ValueError):
        EcommerceSpider.from_crawler(
            crawler,
            urls=["https://a.example"],
            urls_file="https://b.example",
        )


def test_url_invalid():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        EcommerceSpider.from_crawler(crawler, url="foo")


def test_urls(caplog):
    crawler = get_crawler()
    url = "https://example.com"

    spider = EcommerceSpider.from_crawler(crawler, urls=[url])
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_navigation

    spider = EcommerceSpider.from_crawler(crawler, urls=url)
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_navigation

    caplog.clear()
    spider = EcommerceSpider.from_crawler(
        crawler,
        urls="https://a.example\n \nhttps://b.example\nhttps://c.example\nfoo\n\n",
    )
    assert "'foo', from the 'urls' spider argument, is not a valid URL" in caplog.text
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert all(
        request.callback == spider.parse_navigation for request in start_requests
    )
    assert start_requests[0].url == "https://a.example"
    assert start_requests[1].url == "https://b.example"
    assert start_requests[2].url == "https://c.example"

    caplog.clear()
    with pytest.raises(ValueError):
        spider = EcommerceSpider.from_crawler(
            crawler,
            urls="foo\nbar",
        )
    assert "'foo', from the 'urls' spider argument, is not a valid URL" in caplog.text
    assert "'bar', from the 'urls' spider argument, is not a valid URL" in caplog.text


def test_urls_file():
    crawler = get_crawler()
    url = "https://example.com"

    with patch("zyte_spider_templates.params.requests.get") as mock_get:
        response = requests.Response()
        response._content = (
            b"https://a.example\n \nhttps://b.example\nhttps://c.example\n\n"
        )
        mock_get.return_value = response
        spider = EcommerceSpider.from_crawler(crawler, urls_file=url)
        mock_get.assert_called_with(url)

    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert start_requests[0].url == "https://a.example"
    assert start_requests[1].url == "https://b.example"
    assert start_requests[2].url == "https://c.example"


def test_search_queries():
    crawler = get_crawler()
    url = "https://example.com"

    spider = EcommerceSpider.from_crawler(crawler, url=url, search_queries="foo bar")
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_search_request_template
    assert spider.args.search_queries == ["foo bar"]

    spider = EcommerceSpider.from_crawler(crawler, url=url, search_queries="foo\nbar")
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_search_request_template
    assert spider.args.search_queries == ["foo", "bar"]

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, search_queries=["foo", "bar"]
    )
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_search_request_template
    assert spider.args.search_queries == ["foo", "bar"]


def test_search_queries_extract_from():
    crawler = get_crawler()
    url = "https://example.com"

    spider = EcommerceSpider.from_crawler(crawler, url=url, search_queries="foo")
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert "inject" not in start_requests[0].meta

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, search_queries="foo", extract_from="httpResponseBody"
    )
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert "inject" not in start_requests[0].meta

    spider = EcommerceSpider.from_crawler(
        crawler, url=url, search_queries="foo", extract_from="browserHtml"
    )
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].meta["inject"] == [BrowserResponse]


@pytest.mark.parametrize(
    "url,has_full_domain",
    (
        ("https://example.com", (True, True, False, False)),
        ("https://example.com/", (True, True, False, False)),
        ("https://example.com/index.htm", (True, True, False, False)),
        ("https://example.com/index.html", (True, True, False, False)),
        ("https://example.com/index.php", (True, True, False, False)),
        ("https://example.com/home", (True, True, False, False)),
        ("https://example.com/some/category", (False, True, False, False)),
        ("https://example.com/some/category?pid=123", (False, True, False, False)),
    ),
)
def test_get_start_request_default_strategy(url, has_full_domain):
    def assert_meta(has_page_params):
        meta = {"crawling_logs": {"page_type": "productNavigation"}}
        if has_page_params:
            meta["page_params"] = {"full_domain": "example.com"}
        assert result.meta == meta

    for i, crawl_strategy in enumerate(
        ["automatic", "full", "navigation", "pagination_only"]
    ):
        spider = EcommerceSpider.from_crawler(
            get_crawler(), url=url, crawl_strategy=crawl_strategy
        )
        result = spider.get_start_request(url)
        assert result.url == url
        assert result.callback == spider.parse_navigation
        assert_meta(has_full_domain[i])


@pytest.mark.parametrize(
    "crawl_strategy,expected_page_params",
    (
        ("automatic", {}),
        ("full", {"full_domain": "example.com"}),
        ("navigation", {}),
        ("pagination_only", {}),
    ),
)
def test_modify_page_params_for_heuristics(crawl_strategy, expected_page_params):
    url = "https://example.com"
    page_params = {"full_domain": "example.com"}

    spider = EcommerceSpider.from_crawler(
        get_crawler(), url=url, crawl_strategy=crawl_strategy
    )
    page_params = spider._modify_page_params_for_heuristics(page_params)
    assert page_params == expected_page_params
