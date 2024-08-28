from unittest.mock import patch

import pytest
import requests
from pydantic import ValidationError
from scrapy_spider_metadata import get_spider_metadata

from zyte_spider_templates.spiders.serp import SerpSpider

from . import get_crawler
from .test_utils import URL_TO_DOMAIN
from .utils import assertEqualJson


def test_parameters():
    with pytest.raises(ValidationError):
        SerpSpider()

    SerpSpider(url="https://google.com/search?q=foo+bar")
    SerpSpider(url="https://google.com/search?q=foo+bar", max_pages=10)

    with pytest.raises(ValidationError):
        SerpSpider(url="https://google.com/search?q=foo+bar", max_pages="all")


def test_start_requests():
    url = "https://google.com/search?q=foo+bar"
    crawler = get_crawler()
    spider = SerpSpider.from_crawler(crawler, url=url)
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == url
    assert requests[0].callback == spider.parse_serp


def test_metadata():
    actual_metadata = get_spider_metadata(SerpSpider, normalize=True)
    expected_metadata = {
        "template": True,
        "title": "SERP",
        "description": "Template for spiders that extract Google search results.",
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
                        "you can copy and paste it from your browser. Example: https://google.com/search?q=foo+bar"
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
                        "browser. Example: https://google.com/search?q=foo+bar"
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
                        "https://example.com/url-list.txt. The linked list "
                        "must contain 1 URL per line."
                    ),
                    "exclusiveRequired": True,
                    "group": "inputs",
                    "pattern": r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$",
                    "title": "URLs file",
                    "type": "string",
                },
                "max_pages": {
                    "default": 1,
                    "description": "Maximum number of result pages to visit per input URL.",
                    "title": "Pages",
                    "type": "integer",
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
            },
            "title": "SerpSpiderParams",
            "type": "object",
        },
    }
    assertEqualJson(actual_metadata, expected_metadata)


@pytest.mark.parametrize("url,allowed_domain", URL_TO_DOMAIN)
def test_set_allowed_domains(url, allowed_domain):
    crawler = get_crawler()

    kwargs = {"url": url}
    spider = SerpSpider.from_crawler(crawler, **kwargs)
    assert spider.allowed_domains == [allowed_domain]


def test_input_none():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        SerpSpider.from_crawler(crawler)


def test_input_multiple():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        SerpSpider.from_crawler(
            crawler,
            url="https://google.com/search?q=a",
            urls=["https://google.com/search?q=b"],
        )
    with pytest.raises(ValueError):
        SerpSpider.from_crawler(
            crawler,
            url="https://google.com/search?q=a",
            urls_file="https://example.com/input-urls.txt",
        )
    with pytest.raises(ValueError):
        SerpSpider.from_crawler(
            crawler,
            urls=["https://google.com/search?q=b"],
            urls_file="https://example.com/input-urls.txt",
        )


def test_url_invalid():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        SerpSpider.from_crawler(crawler, url="foo")


def test_urls(caplog):
    crawler = get_crawler()
    url = "https://google.com/search?q=foo+bar"

    spider = SerpSpider.from_crawler(crawler, urls=[url])
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_serp

    spider = SerpSpider.from_crawler(crawler, urls=url)
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 1
    assert start_requests[0].url == url
    assert start_requests[0].callback == spider.parse_serp

    caplog.clear()
    spider = SerpSpider.from_crawler(
        crawler,
        urls="https://google.com/search?q=a\n \nhttps://google.com/search?q=b\nhttps://google.com/search?q=c\nfoo\n\n",
    )
    assert "'foo', from the 'urls' spider argument, is not a valid URL" in caplog.text
    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert all(request.callback == spider.parse_serp for request in start_requests)
    assert start_requests[0].url == "https://google.com/search?q=a"
    assert start_requests[1].url == "https://google.com/search?q=b"
    assert start_requests[2].url == "https://google.com/search?q=c"

    caplog.clear()
    with pytest.raises(ValueError):
        spider = SerpSpider.from_crawler(
            crawler,
            urls="foo\nbar",
        )
    assert "'foo', from the 'urls' spider argument, is not a valid URL" in caplog.text
    assert "'bar', from the 'urls' spider argument, is not a valid URL" in caplog.text


def test_urls_file():
    crawler = get_crawler()
    url = "https://example.com/input-urls.txt"

    with patch("zyte_spider_templates.spiders.serp.requests.get") as mock_get:
        response = requests.Response()
        response._content = b"https://google.com/search?q=a\n \nhttps://google.com/search?q=b\nhttps://google.com/search?q=c\n\n"
        mock_get.return_value = response
        spider = SerpSpider.from_crawler(crawler, urls_file=url)
        mock_get.assert_called_with(url)

    start_requests = list(spider.start_requests())
    assert len(start_requests) == 3
    assert start_requests[0].url == "https://google.com/search?q=a"
    assert start_requests[1].url == "https://google.com/search?q=b"
    assert start_requests[2].url == "https://google.com/search?q=c"
