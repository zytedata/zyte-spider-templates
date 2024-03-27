from typing import List, Optional

import attrs
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from web_poet import AnyResponse, PageParams, field, handle_urls
from zyte_common_items import AutoArticleNavigationPage, ProbabilityRequest

from zyte_spider_templates.heuristics import article_filter


@handle_urls("")
@attrs.define
class HeuristicsArticleNavigationPage(AutoArticleNavigationPage):
    response: AnyResponse
    page_params: PageParams
    content_filter = article_filter

    @field
    def subCategories(self) -> Optional[List[ProbabilityRequest]]:
        if self.page_params.get("full_domain"):
            return (
                self.article_navigation.subCategories or []
            ) + self._probably_relevant_links()
        return self.article_navigation.subCategories

    def _urls_for_navigation(self) -> List[str]:
        """Return a list of all URLs in the navigation item:
        - items
        - next page
        - subcategories
        """
        navigation_urls = []
        if self.article_navigation.items:
            navigation_urls.extend(
                [r.url for r in self.article_navigation.subCategories or []]
            )
            navigation_urls.extend([r.url for r in self.article_navigation.items or []])
            if self.article_navigation.nextPage:
                navigation_urls.append(self.article_navigation.nextPage.url)
        return navigation_urls

    def _probably_relevant_links(self) -> List[ProbabilityRequest]:
        default_probability = 0.1

        link_extractor = LinkExtractor(
            allow_domains=self.page_params.get("full_domain")
        )
        ignore_urls = set(self._urls_for_navigation())

        links = []
        response = TextResponse(
            url=str(self.response.url), body=self.response.text.encode()
        )
        for link in link_extractor.extract_links(response):
            if link.url in ignore_urls or link.nofollow:
                continue

            if (
                self.content_filter
                and not self.content_filter.might_be_relevant_content(link.url)
            ):
                continue

            name = (link.text or "").strip()
            request = ProbabilityRequest.from_dict(
                {
                    "url": link.url,
                    "name": f"[heuristics] {name}",
                    "metadata": {"probability": default_probability},
                }
            )
            links.append(request)

        return links
