import json
import logging
from typing import Iterable, List

import attrs
import xtractmime
from scrapy.http import TextResponse
from scrapy.link import Link
from scrapy.linkextractors import LinkExtractor
from web_poet import AnyResponse, HttpResponse, PageParams, Stats, field, handle_urls
from web_poet.utils import cached_method
from zyte_common_items import (
    BaseArticleNavigationPage,
    ProbabilityMetadata,
    ProbabilityRequest,
)

from zyte_spider_templates.feeds import get_feed_urls, parse_feed
from zyte_spider_templates.heuristics import (
    classify_article_crawling_links,
    classify_article_feed_links,
)

from ..heuristics import is_feed_content

logger = logging.getLogger(__name__)


def is_feed_request(request: ProbabilityRequest) -> bool:
    return bool(
        request.name
        and request.name.startswith("[heuristics][articleNavigation][feed]")
    )


@handle_urls("")
@attrs.define
class HeuristicsArticleNavigationPage(BaseArticleNavigationPage):
    response: AnyResponse
    stats: Stats
    page_params: PageParams
    _ARTICLE_HEURISTIC = {"name": "article", "dummy probability": 0.5}
    _NAVIGATION_HEURISTIC = {"name": "subCategories", "dummy probability": 0.5}
    _FEED_HEURISTIC = {"name": "feed", "dummy probability": 1.0}
    _FEED_ITEMS_HEURISTIC = {"name": "feed items", "dummy probability": 0.99}

    @field
    def url(self) -> str:
        return str(self.response.url)

    @field
    def subCategories(self) -> Iterable[ProbabilityRequest]:
        if self._is_response_feed():
            return

        feeds = self._get_feed_links()
        feed_urls = {link.url for link in feeds}
        for link in feeds:
            yield self._get_request(link, self._FEED_HEURISTIC)

        if self.skip_subcategories() or self.is_only_feeds():
            return

        sub_categories = [
            link
            for link in self._get_article_or_navigation_links()
            if link.url not in feed_urls
        ]
        for link in sub_categories:
            yield self._get_request(link, self._NAVIGATION_HEURISTIC)

    @field
    def items(self) -> Iterable[ProbabilityRequest]:
        if self._is_response_feed():
            links = self._get_feed_items_links()
            heuristic = self._FEED_ITEMS_HEURISTIC
        elif not self.is_only_feeds():
            links = self._get_article_or_navigation_links()
            heuristic = self._ARTICLE_HEURISTIC
        else:
            return

        for link in links:
            yield self._get_request(link, heuristic)

    @cached_method
    def _get_article_or_navigation_links(self) -> List[Link]:
        """Extract links from an HTML web page."""
        response = TextResponse(
            url=str(self.response.url), body=self.response.text.encode()
        )
        link_extractor = LinkExtractor()
        links = link_extractor.extract_links(response)
        allowed_links, disallowed_links = classify_article_crawling_links(links)

        _log_and_stats(
            self,
            "heuristic_navigation_or_article",
            links,
            allowed_links,
            disallowed_links,
        )
        return allowed_links

    @cached_method
    def _get_feed_items_links(self) -> List[Link]:
        """Extract links from an RSS/Atom feed."""
        links = [Link(url) for url in parse_feed(self.response)]
        allowed_links, disallowed_links = classify_article_crawling_links(links)

        _log_and_stats(
            self, "heuristic_feed_items", links, allowed_links, disallowed_links
        )
        return allowed_links

    @cached_method
    def _get_feed_links(self) -> List[Link]:
        """Extract links to RSS/Atom feeds form an HTML web page."""
        links = [Link(url) for url in get_feed_urls(self.response)]
        allowed_links, disallowed_links = classify_article_feed_links(links)

        _log_and_stats(self, "heuristic_feed", links, allowed_links, disallowed_links)
        return allowed_links

    @cached_method
    def _is_response_feed(self) -> bool:
        """Return True if a response is an RSS or Atom feed."""

        content_type = ""
        if isinstance(self.response.response, HttpResponse):
            content_type = self.response.response.headers.get("Content-Type", "")
        elif is_feed_content(self.response.response):
            logger.warning(
                "It is likely that the spider is using BrowserHtml to extract the RSS feed. "
                "Please note that using HttpResponse is more efficient."
            )
            return True

        mime_type = xtractmime.extract_mime(
            self.response.text.encode(),
            content_types=(content_type.encode(),),
        )

        return xtractmime.mimegroups.is_xml_mime_type(
            mime_type
        ) or xtractmime.mimegroups.is_json_mime_type(mime_type)

    def _get_request(self, link, heuristic) -> ProbabilityRequest:
        return ProbabilityRequest(
            url=link.url,
            name=f"[heuristics][articleNavigation][{heuristic['name']}] {link.text.strip()}",
            metadata=ProbabilityMetadata(probability=heuristic["dummy probability"]),
        )

    def skip_subcategories(self) -> bool:
        return self.page_params.get("skip_subcategories", False)

    def is_only_feeds(self) -> bool:
        return self.page_params.get("only_feeds", False)


def _log_and_stats(self, urls_type, links, allowed_links, disallowed_links):
    _logs(self, urls_type, links, allowed_links, disallowed_links)
    _stats(self, urls_type, links, allowed_links, disallowed_links)


def _stats(page, urls_type, urls, allowed_urls, disallowed_urls):
    page.stats.inc(f"article_spider/{urls_type}/visited", 1)
    page.stats.inc(f"article_spider/{urls_type}/no_links", 0 if urls else 1)
    page.stats.inc(f"article_spider/{urls_type}/with_links", 1 if urls else 0)
    page.stats.inc(f"article_spider/{urls_type}/links/total", len(urls))
    page.stats.inc(f"article_spider/{urls_type}/links/allow", len(allowed_urls))
    page.stats.inc(f"article_spider/{urls_type}/links/disallow", len(disallowed_urls))


def _logs(page, urls_type, urls, allowed_urls, disallowed_urls):
    page_name = page.item_cls.__name__
    data = {
        "page": page_name,
        "page url": page.url,
        "urls type": urls_type,
        "urls found": len(urls),
        "allowed urls": len(allowed_urls),
        "urls to skip": len(disallowed_urls),
        "list of urls to skip": [
            url.url if isinstance(url, Link) else url for url in disallowed_urls
        ],
    }
    logger.debug(f"Article Heuristic Logs:\n{json.dumps(data, indent=2)}")
