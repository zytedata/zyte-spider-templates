from typing import List, Optional

import attrs
from scrapy.http import TextResponse
from scrapy.linkextractors import LinkExtractor
from web_poet import HttpResponse, PageParams, field, handle_urls
from zyte_common_items import (
    BaseProductNavigationPage,
    ProbabilityRequest,
    ProductNavigation,
    Request,
)

from zyte_spider_templates.heuristics import might_be_category


@handle_urls("")
@attrs.define
class HeuristicsProductNavigationPage(BaseProductNavigationPage):
    # TODO: swap with BrowserResponse after evaluating it.
    # Also after when the following issue has been fixed:
    # https://github.com/scrapy-plugins/scrapy-zyte-api/issues/91#issuecomment-1744305554
    # NOTE: Even with BrowserResponse, it would still send separate
    # requests for it and productNavigation.
    response: HttpResponse
    navigation_item: ProductNavigation
    page_params: PageParams

    # FIXME: Remove boilerplate code when this feature is released:
    # https://github.com/scrapinghub/scrapy-poet/issues/168

    @field
    def categoryName(self) -> Optional[str]:
        return self.navigation_item.categoryName

    @field
    def pageNumber(self) -> Optional[int]:
        return self.navigation_item.pageNumber

    @field
    def items(self) -> Optional[List[ProbabilityRequest]]:
        return self.navigation_item.items

    @field
    def nextPage(self) -> Optional[Request]:
        return self.navigation_item.nextPage

    @field
    def subCategories(self) -> Optional[List[ProbabilityRequest]]:
        if self.page_params.get("full_domain"):
            return (
                self.navigation_item.subCategories or []
            ) + self._probably_category_links()
        return self.navigation_item.subCategories

    def _urls_for_category(self) -> List[str]:
        """Return a list of all URLs in the ProductNavigation item:
        - items
        - next page
        - subcategories
        """

        category_urls = []
        if self.navigation_item.items:
            category_urls.extend(
                [r.url for r in self.navigation_item.subCategories or []]
            )
            category_urls.extend([r.url for r in self.navigation_item.items or []])
            if self.navigation_item.nextPage:
                category_urls.append(self.navigation_item.nextPage.url)
        return category_urls

    def _probably_category_links(self) -> List[ProbabilityRequest]:
        # TODO: This should be tuned later
        default_probability = 0.1

        link_extractor = LinkExtractor(
            allow_domains=self.page_params.get("full_domain")
        )
        ignore_urls = set(self._urls_for_category())

        links = []
        response = TextResponse(url=str(self.response.url), body=self.response.body)
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
