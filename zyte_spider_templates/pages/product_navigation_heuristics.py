from typing import List, Optional

import attrs
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from web_poet import AnyResponse, PageParams, field, handle_urls
from zyte_common_items import AutoProductNavigationPage, ProbabilityRequest

from zyte_spider_templates.heuristics import might_be_category


@handle_urls("")
@attrs.define
class HeuristicsProductNavigationPage(AutoProductNavigationPage):
    response: AnyResponse
    page_params: PageParams

    @field
    def subCategories(self) -> Optional[List[ProbabilityRequest]]:
        if self.page_params.get("full_domain"):
            return (
                self.product_navigation.subCategories or []
            ) + self._probably_category_links()
        return self.product_navigation.subCategories

    def _urls_for_category(self) -> List[str]:
        """Return a list of all URLs in the ProductNavigation item:
        - items
        - next page
        - subcategories
        """

        category_urls = []
        if self.product_navigation.items:
            category_urls.extend(
                [r.url for r in self.product_navigation.subCategories or []]
            )
            category_urls.extend([r.url for r in self.product_navigation.items or []])
            if self.product_navigation.nextPage:
                category_urls.append(self.product_navigation.nextPage.url)
        return category_urls

    def _probably_category_links(self) -> List[ProbabilityRequest]:
        # TODO: This should be tuned later
        default_probability = 0.1

        link_extractor = LinkExtractor(
            allow_domains=self.page_params.get("full_domain", [])
        )
        ignore_urls = set(self._urls_for_category())

        links = []
        response = TextResponse(
            url=str(self.response.url), body=self.response.text.encode()
        )
        for link in link_extractor.extract_links(response):
            if link.url in ignore_urls:
                continue

            # TODO: Convert to a configurable parameter like 'obey_nofollow_links'
            # some time after the MVP launch.
            if link.nofollow:
                continue

            if not might_be_category(link.url):
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
