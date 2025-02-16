import logging
from unittest.mock import MagicMock, call, patch

import pytest
import requests
import scrapy
from pydantic import ValidationError
from pytest_twisted import ensureDeferred
from scrapy import signals
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import get_spider_metadata
from zyte_common_items import JobPosting, JobPostingNavigation, ProbabilityRequest

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS,
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.spiders.job_posting import (
    JobPostingCrawlStrategy,
    JobPostingSpider,
)

from . import get_crawler
from .test_utils import URL_TO_DOMAIN
from .utils import assertEqualSpiderMetadata


def test_parameters():
    with pytest.raises(ValidationError):
        JobPostingSpider()

    JobPostingSpider(url="https://example.com")
    JobPostingSpider(
        url="https://example.com", crawl_strategy=JobPostingCrawlStrategy.direct_item
    )
    JobPostingSpider(url="https://example.com", crawl_strategy="direct_item")

    with pytest.raises(ValidationError):
        JobPostingSpider(url="https://example.com", crawl_strategy="unknown")


def test_start_requests():
    url = "https://example.com"
    crawler = get_crawler()
    spider = JobPostingSpider.from_crawler(crawler, url=url)
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == url
    assert requests[0].callback == spider.parse_navigation


def test_crawl():
    crawler = get_crawler()
    url = "https://example.com/category/tech"
    nextpage_url = "https://example.com/category/tech?p=2"
    item_urls = [
        "https://example.com/job?id=123",
        "https://example.com/job?id=988",
    ]
    request = scrapy.Request("https://example.com")
    response = DummyResponse(url=url, request=request)

    nextpage = {"nextPage": {"url": nextpage_url}}
    items = {
        "items": [
            {"url": item_urls[0], "metadata": {"probability": 0.99}},
            {"url": item_urls[1], "metadata": {"probability": 0.83}},
        ],
    }
    spider = JobPostingSpider.from_crawler(crawler, url="https://example.com/")

    # no links found
    navigation = JobPostingNavigation.from_dict({"url": url})
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 0

    # nextpage + items
    navigation = JobPostingNavigation.from_dict(
        {
            "url": url,
            **nextpage,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 3
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_job_posting
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_job_posting
    assert requests[2].url == nextpage_url
    assert requests[2].callback == spider.parse_navigation

    # nextpage
    navigation = JobPostingNavigation.from_dict(
        {
            "url": url,
            **nextpage,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 0

    # items
    navigation = JobPostingNavigation.from_dict(
        {
            "url": url,
            **items,
        }
    )
    requests = list(spider.parse_navigation(response, navigation))
    assert len(requests) == 2
    assert requests[0].url == item_urls[0]
    assert requests[0].callback == spider.parse_job_posting
    assert requests[1].url == item_urls[1]
    assert requests[1].callback == spider.parse_job_posting


def test_crawl_strategy_direct_item():
    crawler = get_crawler()
    spider = JobPostingSpider.from_crawler(
        crawler,
        url="https://example.com",
        crawl_strategy="direct_item",
    )
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].callback == spider.parse_job_posting


@pytest.mark.parametrize(
    "probability,has_item,item_drop",
    ((0.9, True, False), (0.09, False, True), (0.1, True, False), (None, True, False)),
)
def test_parse_job_posting(probability, has_item, item_drop, caplog):
    caplog.clear()

    job_posting_url = "https://example.com/job?id=123"
    job_posting = JobPosting.from_dict(
        {"url": job_posting_url, "metadata": {"probability": probability}}
    )
    response = DummyResponse(job_posting_url)
    spider = JobPostingSpider(url="https://example.com")
    mock_crawler = MagicMock()
    spider.crawler = mock_crawler
    logging.getLogger().setLevel(logging.INFO)
    items = list(spider.parse_job_posting(response, job_posting, DynamicDeps()))
    if item_drop:
        assert mock_crawler.method_calls == [
            call.stats.inc_value("drop_item/job_posting/low_probability")
        ]

    if has_item:
        assert len(items) == 1
        assert items[0] == job_posting
        assert caplog.text == ""
    else:
        assert len(items) == 0
        assert str(job_posting) in caplog.text


def test_arguments():
    # Ensure passing no arguments works.
    crawler = get_crawler()

    # Needed since it's a required argument.
    base_kwargs = {"url": "https://example.com"}

    JobPostingSpider.from_crawler(crawler, **base_kwargs)

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
                "jobPostingOptions": {"extractFrom": "browserHtml"},
                "jobPostingNavigationOptions": {"extractFrom": "browserHtml"},
            },
        ),
        (
            "extract_from",
            "httpResponseBody",
            "ZYTE_API_PROVIDER_PARAMS",
            {"geolocation": "US"},
            "getdict",
            {
                "jobPostingOptions": {"extractFrom": "httpResponseBody"},
                "jobPostingNavigationOptions": {"extractFrom": "httpResponseBody"},
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
        spider = JobPostingSpider.from_crawler(crawler, **kwargs, **base_kwargs)
        getter = getattr(crawler.settings, getter_name)
        assert getter(setting) == new_setting_value
        assert spider.allowed_domains == ["example.com"]


def test_metadata():
    actual_metadata = get_spider_metadata(JobPostingSpider, normalize=True)
    expected_metadata = {
        "template": True,
        "title": "Job posting",
        "description": "[Experimental] Template for spiders that extract job posting data from websites.",
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
                "crawl_strategy": {
                    "default": "navigation",
                    "description": (
                        "Determines how input URLs and follow-up URLs are crawled."
                    ),
                    "enumMeta": {
                        "navigation": {
                            "description": (
                                "Follow pagination and job posting detail pages."
                            ),
                            "title": "Navigation",
                        },
                        "direct_item": {
                            "description": (
                                "Treat input URLs as direct links to job posting detail pages, and "
                                "extract a job posting from each."
                            ),
                            "title": "Direct URLs to job postings",
                        },
                    },
                    "title": "Crawl strategy",
                    "enum": [
                        "navigation",
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
            "title": "JobPostingSpiderParams",
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
    spider = JobPostingSpider.from_crawler(crawler, **base_kwargs)
    request = ProbabilityRequest(url="https://example.com")
    scrapy_request = spider.get_parse_job_posting_request(request)
    assert scrapy_request.meta.get("allow_offsite") is True


def test_get_nextpage_request():
    url = "https://example.com"

    # Minimal Args
    request = ProbabilityRequest(url=url)
    spider = JobPostingSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore

    scrapy_request = spider.get_nextpage_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {"name": "", "probability": None, "page_type": "nextPage"},
    }


def test_get_parse_navigation_request():
    url = "https://example.com"

    # Minimal args
    request = ProbabilityRequest(url=url)
    spider = JobPostingSpider(url="https://example.com")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation  # type: ignore

    scrapy_request = spider.get_parse_navigation_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "",
            "probability": None,
            "page_type": "jobPostingNavigation",
        },
    }


@pytest.mark.parametrize("url,allowed_domain", URL_TO_DOMAIN)
def test_set_allowed_domains(url, allowed_domain):
    crawler = get_crawler()

    kwargs = {"url": url}
    spider = JobPostingSpider.from_crawler(crawler, **kwargs)
    assert spider.allowed_domains == [allowed_domain]


def test_input_none():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        JobPostingSpider.from_crawler(crawler)


def test_input_multiple():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        JobPostingSpider.from_crawler(
            crawler,
            url="https://a.example",
            urls=["https://b.example"],
        )
    with pytest.raises(ValueError):
        JobPostingSpider.from_crawler(
            crawler,
            url="https://a.example",
            urls_file="https://b.example",
        )
    with pytest.raises(ValueError):
        JobPostingSpider.from_crawler(
            crawler,
            urls=["https://a.example"],
            urls_file="https://b.example",
        )


def test_url_invalid():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        JobPostingSpider.from_crawler(crawler, url="foo")


def test_urls(caplog):
    crawler = get_crawler()
    url = "https://example.com"

    spider = JobPostingSpider.from_crawler(crawler, urls=[url])
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_navigation

    spider = JobPostingSpider.from_crawler(crawler, urls=url)
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_navigation

    caplog.clear()
    spider = JobPostingSpider.from_crawler(
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
        JobPostingSpider.from_crawler(
            crawler,
            urls="foo\nbar",
        )
    assert "'foo', from the 'urls' spider argument, is not a valid URL" in caplog.text
    assert "'bar', from the 'urls' spider argument, is not a valid URL" in caplog.text


def test_urls_file():
    crawler = get_crawler()
    url = "https://example.com"

    with patch("zyte_spider_templates.spiders.job_posting.requests.get") as mock_get:
        response = requests.Response()
        response._content = (
            b"https://a.example\n \nhttps://b.example\nhttps://c.example\n\n"
        )
        mock_get.return_value = response
        spider = JobPostingSpider.from_crawler(crawler, urls_file=url)
        mock_get.assert_called_with(url)

    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert start_requests[0].url == "https://a.example"
    assert start_requests[1].url == "https://b.example"
    assert start_requests[2].url == "https://c.example"


@ensureDeferred
async def test_offsite(mockserver):
    settings = {
        "ZYTE_API_URL": mockserver.urljoin("/"),
        "ZYTE_API_KEY": "a",
        "ADDONS": {
            "scrapy_zyte_api.Addon": 500,
            "zyte_spider_templates.Addon": 1000,
        },
    }
    crawler = get_crawler(settings=settings, spider_cls=JobPostingSpider)
    actual_output = set()

    def track_item(item, response, spider):
        actual_output.add(item.url)

    crawler.signals.connect(track_item, signal=signals.item_scraped)
    await crawler.crawl(url="https://jobs.example")
    assert actual_output == {
        "https://jobs.offsite.example/jobs/1",
        "https://jobs.offsite.example/jobs/2",
    }
