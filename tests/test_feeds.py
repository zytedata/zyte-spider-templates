from typing import List, Union

import pytest
from web_poet import (
    AnyResponse,
    BrowserHtml,
    BrowserResponse,
    HttpResponse,
    HttpResponseBody,
    ResponseUrl,
)

from zyte_spider_templates.feeds import get_feed_urls, parse_feed, unique_urls


@pytest.fixture
def sample_urls() -> List[str]:
    return [
        "http://example.com",
        "http://example.com/",
        "https://example.com",
        "https://example.com/",
        "http://example.com/page",
        "http://example.com/page/",
    ]


def test_unique_urls(sample_urls):
    unique_list = unique_urls(sample_urls)
    assert len(unique_list) == 4


def test_unique_urls_order(sample_urls):
    unique_list = unique_urls(sample_urls)
    expected_order = [
        "http://example.com",
        "https://example.com",
        "http://example.com/page",
        "http://example.com/page/",
    ]
    assert unique_list == expected_order


@pytest.fixture
def sample_response_feed() -> Union[AnyResponse, HttpResponse, BrowserResponse]:
    html_content = """
    <html>
    <head>
        <link rel="alternate" type="application/rss+xml" href="http://example.com/rss.xml">
        <link rel="alternate" type="application/atom+xml" href="http://example.com/atom.xml">
    </head>
    <body>
        <a href="http://example.com/feed/rss.xml">RSS Feed</a>
        <a href="http://example.com/feed/atom.xml">Atom Feed</a>
    </body>
    </html>
    """
    return HttpResponse(
        url=ResponseUrl("http://example.com"),
        body=HttpResponseBody(html_content.encode(encoding="utf-8")),
    )


def test_get_feed_urls(sample_response_feed):
    feed_urls = get_feed_urls(sample_response_feed)
    assert len(feed_urls) == 3
    assert "http://example.com/rss.xml" in feed_urls
    assert "http://example.com/atom.xml" in feed_urls
    assert "http://example.com/feed/rss.xml" in feed_urls


@pytest.fixture
def sample_response_feeds() -> Union[AnyResponse, HttpResponse, BrowserResponse]:
    rss_content = """
    <rss version="2.0">
    <channel>
        <title>Sample RSS Feed</title>
        <link>http://example.com/feed/rss.xml</link>
        <description>This is a sample RSS feed</description>
        <item>
            <title>Item 1</title>
            <link>http://example.com/item1</link>
            <description>Description of Item 1</description>
        </item>
        <item>
            <title>Item 2</title>
            <link>http://example.com/item2</link>
            <description>Description of Item 2</description>
        </item>
        <item>
            <title>Item 3</title>
            <link>http://example.com/item2</link>
            <description>Description of Item 3</description>
        </item>
    </channel>
    </rss>
    """
    return HttpResponse(
        url=ResponseUrl("http://example.com/feed/rss.xml"),
        body=HttpResponseBody(rss_content.encode(encoding="utf-8")),
    )


@pytest.mark.parametrize("is_browser_response", [False, True])
def test_parse_feed(sample_response_feeds, is_browser_response):
    if is_browser_response:
        sample_response_feeds = BrowserResponse(
            url=ResponseUrl("http://example.com"),
            html=BrowserHtml(str(sample_response_feeds.text)),
        )
    feed_urls = parse_feed(sample_response_feeds)
    expected_urls = ["http://example.com/item1", "http://example.com/item2"]
    assert feed_urls == expected_urls
