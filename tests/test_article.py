from typing import Tuple, Type, cast
from unittest.mock import patch

import pytest
import requests
import scrapy
from pydantic import ValidationError
from scrapy.statscollectors import StatsCollector
from scrapy_poet import DummyResponse
from scrapy_spider_metadata import get_spider_metadata
from zyte_common_items import (
    Article,
    ArticleNavigation,
    ProbabilityMetadata,
    ProbabilityRequest,
    Request,
)

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS,
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.params import ExtractFrom
from zyte_spider_templates.spiders.article import (
    ArticleCrawlStrategy,
    ArticleSpider,
    RequestType,
)

from . import get_crawler
from .utils import assertEqualSpiderMetadata


@pytest.mark.parametrize(
    "input_data, expected_exception",
    (
        ({"url": "https://example.com"}, (None, "")),
        ({"urls_file": "https://example.com/list.txt"}, (None, "")),
        (
            {
                "url": "https://example.com",
                "crawl_strategy": ArticleCrawlStrategy.full,
            },
            (None, ""),
        ),
        ({"url": "https://example.com", "crawl_strategy": "full"}, (None, "")),
        ({"url": "https://example.com", "max_requests_per_seed": 1000}, (None, "")),
        ({"url": "https://example.com", "max_requests_per_seed": 0}, (None, "")),
        (
            {"url": "https://example.com", "max_requests_per_seed": -1},
            (
                ValidationError,
                ("max_requests_per_seed\n  Input should be greater than or equal to 0"),
            ),
        ),
        (
            {"url": "https://example.com", "extract_from": ExtractFrom.browserHtml},
            (None, ""),
        ),
        ({"url": "https://example.com", "extract_from": "browserHtml"}, (None, "")),
        (
            {
                "some_field": "https://a.example.com\nhttps://b.example.com\nhttps://c.example.com"
            },
            (
                ValidationError,
                "Value error, No input parameter defined. Please, define one of: url, urls...",
            ),
        ),
        (
            {"url": {"url": "https://example.com"}},
            (ValidationError, "url\n  Input should be a valid string"),
        ),
        (
            {"url": ["https://example.com"]},
            (ValidationError, "url\n  Input should be a valid string"),
        ),
        (
            {"urls": "https://example.com", "crawl_strategy": "unknown"},
            (ValidationError, "crawl_strategy\n  Input should be 'full'"),
        ),
        (
            {"url": "https://example.com", "urls_file": "https://example.com/list.txt"},
            (ValidationError, "Value error, Expected a single input parameter, got 2:"),
        ),
        ({"url": "wrong_url"}, (ValidationError, "url\n  String should match pattern")),
    ),
)
def test_parameters(input_data, expected_exception: Tuple[Type[Exception], str]):
    exception: Type[Exception] = expected_exception[0]
    if exception:
        with pytest.raises(exception) as e:
            ArticleSpider(**input_data)
        assert expected_exception[1] in str(e)
    else:
        ArticleSpider(**input_data)


def test_crawl_strategy_direct_item():
    crawler = get_crawler()
    spider = ArticleSpider.from_crawler(
        crawler,
        url="https://example.com",
        crawl_strategy="direct_item",
    )
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].callback == cast(ArticleSpider, spider).parse_dynamic
    assert start_requests[0].url == "https://example.com"
    assert start_requests[0].meta["request_type"] == RequestType.ARTICLE
    assert start_requests[0].meta["crawling_logs"]["name"] == "[article]"
    assert start_requests[0].meta["crawling_logs"]["page_type"] == "article"
    assert start_requests[0].meta["crawling_logs"]["probability"] == 1.0


def test_arguments():
    crawler = get_crawler()
    base_kwargs = {"url": "https://example.com"}
    ArticleSpider.from_crawler(crawler, **base_kwargs)

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
                "articleOptions": {"extractFrom": "browserHtml"},
                "articleNavigationOptions": {"extractFrom": "browserHtml"},
            },
        ),
        (
            "extract_from",
            "httpResponseBody",
            "ZYTE_API_PROVIDER_PARAMS",
            {"geolocation": "US"},
            "getdict",
            {
                "articleOptions": {"extractFrom": "httpResponseBody"},
                "articleNavigationOptions": {"extractFrom": "httpResponseBody"},
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
        ArticleSpider.from_crawler(crawler, **kwargs, **base_kwargs)
        getter = getattr(crawler.settings, getter_name)
        assert getter(setting) == new_setting_value


def test_init_input_with_urls_file():
    crawler = get_crawler()
    url = "https://example.com"

    with patch("zyte_spider_templates.spiders.article.requests.get") as mock_get:
        response = requests.Response()
        response._content = (
            b"https://a.example\n \nhttps://b.example\nhttps://c.example\n\n"
        )
        mock_get.return_value = response
        spider = ArticleSpider.from_crawler(crawler, urls_file=url)
        mock_get.assert_called_with(url)

    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert start_requests[0].url == "https://a.example"
    assert start_requests[1].url == "https://b.example"
    assert start_requests[2].url == "https://c.example"


def test_init_input_without_urls_file():
    crawler = get_crawler()
    base_kwargs = {"url": "https://example.com"}
    spider = ArticleSpider.from_crawler(crawler, **base_kwargs)
    cast(ArticleSpider, spider)._init_input()

    assert spider.start_urls == ["https://example.com"]


def test_metadata():
    actual_metadata = get_spider_metadata(ArticleSpider, normalize=True)
    expected_metadata = {
        "template": True,
        "title": "Article",
        "description": "[Experimental] Template for spiders that extract article data from news or blog websites.",
        "param_schema": {
            "groups": [
                {
                    "description": "Input data that determines the "
                    "start URLs of the crawl.",
                    "id": "inputs",
                    "title": "Inputs",
                    "widget": "exclusive",
                }
            ],
            "properties": {
                "url": {
                    "default": "",
                    "description": "Initial URL for the "
                    "crawl. Enter the full "
                    "URL including "
                    "http(s), you can copy "
                    "and paste it from "
                    "your browser. "
                    "Example: "
                    "https://toscrape.com/",
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "pattern": "^https?://[^:/\\s]+(:\\d{1,5})?(/[^\\s]*)*(#[^\\s]*)?$",
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
                        "URL that point to a plain-text file with a list of URLs to "
                        "crawl, e.g. https://example.com/url-list.txt. The linked file "
                        "must contain 1 URL per line."
                    ),
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "pattern": "^https?://[^:/\\s]+(:\\d{1,5})?(/[^\\s]*)*(#[^\\s]*)?$",
                    "title": "URLs file",
                    "type": "string",
                },
                "incremental": {
                    "default": False,
                    "description": (
                        "Skip items with URLs already stored in the specified Zyte Scrapy Cloud Collection. "
                        "This feature helps avoid reprocessing previously crawled items and requests by comparing "
                        "their URLs against the stored collection."
                    ),
                    "title": "Incremental",
                    "type": "boolean",
                },
                "incremental_collection_name": {
                    "anyOf": [
                        {"type": "string", "pattern": "^[a-zA-Z0-9_]+$"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": "Name of the Zyte Scrapy Cloud Collection used during an incremental crawl."
                    "By default, a Collection named after the spider (or virtual spider) is used, "
                    "meaning that matching URLs from previous runs of the same spider are skipped, "
                    "provided those previous runs had `incremental` argument set to `true`."
                    "Using a different collection name makes sense, for example, in the following cases:"
                    "- different spiders share a collection."
                    "- the same spider uses different collections (e.g., for development runs vs. production runs). "
                    "Only ASCII alphanumeric characters and underscores are allowed in the collection name.",
                    "title": "Incremental Collection Name",
                },
                "crawl_strategy": {
                    "default": "full",
                    "description": (
                        "Determines how input URLs and follow-up URLs are crawled."
                    ),
                    "enumMeta": {
                        "direct_item": {
                            "description": (
                                "Treat input URLs as direct links to "
                                "articles, and extract an article from each."
                            ),
                            "title": "Direct URLs to Articles",
                        },
                        "full": {
                            "description": (
                                "Follow most links within each domain from the list of URLs in an "
                                "attempt to discover and extract as many articles as possible."
                            ),
                            "title": "Full",
                        },
                    },
                    "title": "Crawl Strategy",
                    "enum": ["full", "direct_item"],
                    "type": "string",
                },
                "geolocation": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": ("Country of the IP addresses to use."),
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
                "max_requests_per_seed": {
                    "anyOf": [{"minimum": 0, "type": "integer"}, {"type": "null"}],
                    "default": None,
                    "description": (
                        "The maximum number of follow-up requests allowed per "
                        "initial URL. Unlimited if not set."
                    ),
                    "title": "Max requests per seed",
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
            },
            "title": "ArticleSpiderParams",
            "type": "object",
        },
    }
    assertEqualSpiderMetadata(actual_metadata, expected_metadata)

    geolocation = actual_metadata["param_schema"]["properties"]["geolocation"]
    assert geolocation["enum"][0] == "AF"
    assert geolocation["enumMeta"]["UY"] == {"title": "Uruguay (UY)"}
    assert set(geolocation["enum"]) == set(geolocation["enumMeta"])


def test_crawl():
    url = "https://example.com/article_list"
    article_url = "https://example.com/article_page"
    item_urls = [
        ("https://example.com/link_1", "article", 0.5),
        ("https://example.com/link_2", "article", 0.5),
        ("https://example.com/link_4", "feed items", 0.99),
    ]
    subcategory_urls = [
        ("https://example.com/link_1", "subCategories", 0.5),
        ("https://example.com/link_2", "subCategories", 0.5),
        ("https://example.com/link_3", "feed", 1.0),
    ]

    article_navigation_items = {
        "items": [
            ProbabilityRequest(
                url=item_url,
                name=f"[heuristics][articleNavigation][{heuristic_name}] {item_url.split('/')[-1]}",
                metadata=ProbabilityMetadata(probability=probability),
            )
            for item_url, heuristic_name, probability in item_urls
        ],
        "subCategories": [
            ProbabilityRequest(
                url=subcategory_url,
                name=f"[heuristics][articleNavigation][{heuristic_name}] {subcategory_url.split('/')[-1]}",
                metadata=ProbabilityMetadata(probability=probability),
            )
            for subcategory_url, heuristic_name, probability in subcategory_urls
        ],
    }

    crawler = get_crawler()
    crawler.stats = StatsCollector(crawler)
    spider = ArticleSpider.from_crawler(crawler, url=url)

    # start_requests -> get_seed_request
    requests = list(spider.start_requests())
    requests[0].meta["crawling_logs"] = {
        "name": "[seed]",
        "page_type": "articleNavigation",
        "probability": None,
    }
    requests[0].meta["page_type"] = "articleNavigation"
    requests[0].meta["request_type"] = RequestType.SEED

    # parse_navigation
    request = scrapy.Request(url=url)
    response = DummyResponse(url=request.url, request=request)
    navigation = ArticleNavigation(
        url="",
        items=article_navigation_items["items"],
        subCategories=article_navigation_items["subCategories"],
    )
    requests = list(
        cast(ArticleSpider, spider).parse_dynamic(
            response, {ArticleNavigation: navigation}
        )
    )
    assert requests[2].url == "https://example.com/link_4"
    assert requests[2].meta["request_type"] == RequestType.ARTICLE
    assert (
        requests[2].meta["crawling_logs"]["name"]
        == "[heuristics][articleNavigation][feed items] link_4"
    )
    assert requests[2].meta["crawling_logs"]["page_type"] == "article"
    assert requests[2].meta["crawling_logs"]["probability"] == 0.99
    assert requests[2].callback == cast(ArticleSpider, spider).parse_dynamic

    assert requests[5].url == "https://example.com/link_3"
    assert requests[5].meta["request_type"] == RequestType.NAVIGATION
    assert (
        requests[5].meta["crawling_logs"]["name"]
        == "[heuristics][articleNavigation][feed] link_3"
    )
    assert requests[5].meta["crawling_logs"]["page_type"] == "subCategories"
    assert requests[5].meta["crawling_logs"]["probability"] == 1.0
    assert requests[5].callback == cast(ArticleSpider, spider).parse_dynamic

    assert requests[0].url == "https://example.com/link_1"
    assert requests[0].meta["request_type"] == RequestType.ARTICLE_AND_NAVIGATION
    assert (
        requests[0].meta["crawling_logs"]["name"] == "[article or subCategories] link_1"
    )
    assert (
        requests[0].meta["crawling_logs"]["page_type"] == "articleNavigation-heuristics"
    )
    assert requests[0].meta["crawling_logs"]["probability"] == 0.5
    assert requests[0].callback == cast(ArticleSpider, spider).parse_dynamic

    assert requests[1].url == "https://example.com/link_2"
    assert requests[1].meta["request_type"] == RequestType.ARTICLE_AND_NAVIGATION
    assert (
        requests[1].meta["crawling_logs"]["name"] == "[article or subCategories] link_2"
    )
    assert (
        requests[1].meta["crawling_logs"]["page_type"] == "articleNavigation-heuristics"
    )
    assert requests[1].meta["crawling_logs"]["probability"] == 0.5
    assert requests[1].callback == cast(ArticleSpider, spider).parse_dynamic

    # parse_article
    request = scrapy.Request(url=url)
    response = DummyResponse(url=request.url, request=request)
    article = Article(url=article_url)
    assert (
        article
        == list(
            cast(ArticleSpider, spider).parse_dynamic(response, {Article: article})
        )[0]
    )

    # parse article_and_navigation
    request = scrapy.Request(url=url)
    response = DummyResponse(url=request.url, request=request)
    article = Article(url=article_url)
    navigation = ArticleNavigation(
        url="",
        items=article_navigation_items["items"],
        subCategories=article_navigation_items["subCategories"],
    )
    requests = list(
        cast(ArticleSpider, spider).parse_dynamic(
            response, {Article: article, ArticleNavigation: navigation}
        )
    )

    assert requests[0] == article
    assert requests[1].url == "https://example.com/link_1"
    assert requests[2].url == "https://example.com/link_2"
    assert requests[3].url == "https://example.com/link_4"
    assert requests[4].url == "https://example.com/link_1"
    assert requests[5].url == "https://example.com/link_2"
    assert requests[6].url == "https://example.com/link_3"

    # parse_article_and_navigation with article, with next_page and with items
    request = scrapy.Request(url=url)
    response = DummyResponse(url=request.url, request=request)
    article = Article(url=article_url)
    navigation = ArticleNavigation(
        url="",
        items=article_navigation_items["items"],
        subCategories=article_navigation_items["subCategories"],
        nextPage=Request(url="https://example.com/next_page", name="nextPage"),
    )
    requests = list(
        cast(ArticleSpider, spider).parse_dynamic(
            response, {Article: article, ArticleNavigation: navigation}
        )
    )

    assert requests[0] == article
    assert requests[1].url == "https://example.com/next_page"
    assert requests[1].meta["request_type"] == RequestType.NEXT_PAGE
    assert requests[2].url == "https://example.com/link_1"
    assert requests[3].url == "https://example.com/link_2"
    assert requests[4].url == "https://example.com/link_4"
    assert requests[5].url == "https://example.com/link_1"
    assert requests[6].url == "https://example.com/link_2"
    assert requests[7].url == "https://example.com/link_3"

    # parse_article_and_navigation with article, with next_page and without items
    request = scrapy.Request(url=url)
    response = DummyResponse(url=request.url, request=request)
    article = Article(url=article_url)
    navigation = ArticleNavigation(
        url="",
        items=[],
        subCategories=article_navigation_items["subCategories"],
        nextPage=Request(url="https://example.com/next_page", name="nextPage"),
    )
    requests = list(
        cast(ArticleSpider, spider).parse_dynamic(
            response, {Article: article, ArticleNavigation: navigation}
        )
    )

    assert requests[0] == article
    assert requests[1].url == "https://example.com/link_1"
    assert requests[2].url == "https://example.com/link_2"
    assert requests[3].url == "https://example.com/link_3"
