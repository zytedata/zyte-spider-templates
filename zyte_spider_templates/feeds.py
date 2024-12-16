from typing import List, Set, Union

import feedparser
from scrapy.utils.python import unique
from w3lib.html import strip_html5_whitespace
from w3lib.url import canonicalize_url
from web_poet import AnyResponse, BrowserResponse, HttpResponse, RequestUrl, ResponseUrl


def unique_urls(urls: List[str]) -> List[str]:
    return unique(urls, key=canonicalize_url)


def get_feed_urls(
    response: Union[AnyResponse, HttpResponse, BrowserResponse]
) -> Set[str]:
    """Find all RSS or Atom feeds from a page"""
    feed_urls = set()

    for link in response.xpath("//link[@type]"):
        link_type: str = strip_html5_whitespace(link.attrib["type"])
        link_href: Union[str, RequestUrl, ResponseUrl] = strip_html5_whitespace(
            link.attrib.get("href", "")
        )
        if link_href:
            link_href = response.urljoin(link_href)
            rss_url = atom_url = None
            if "rss+xml" in link_type:
                rss_url = link_href
            elif "atom+xml" in link_type:
                atom_url = link_href
            feed_url = rss_url or atom_url
            if feed_url:
                feed_urls.add(str(feed_url))

    for link in response.xpath("//a/@href").getall():
        link_href = strip_html5_whitespace(link)
        if link_href.endswith("rss.xml"):
            feed_urls.add(str(response.urljoin(link_href)))

    return feed_urls


def parse_feed(
    response: Union[AnyResponse, HttpResponse, BrowserResponse]
) -> List[str]:
    response_text = (
        str(response.html) if isinstance(response, BrowserResponse) else response.text
    )

    feed = feedparser.parse(response_text)
    urls = [
        strip_html5_whitespace(entry.get("link", ""))
        for entry in feed.get("entries", [])
    ]
    return unique_urls([str(response.urljoin(url)) for url in urls if url])
