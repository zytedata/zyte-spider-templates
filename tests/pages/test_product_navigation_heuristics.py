import pytest
from pytest_twisted import ensureDeferred
from web_poet import AnyResponse, HttpResponse, PageParams, RequestUrl
from zyte_common_items import ProbabilityRequest, ProductNavigation

from zyte_spider_templates.pages.product_navigation_heuristics import (
    HeuristicsProductNavigationPage,
)


@ensureDeferred
async def test_unknown_product_page():
    body = b"""
        <html>
        <body>
            <div>
                <h1>Subcategories<h1>
                <div>
                    <a href="https://example.com/categ/sentinels">Sentinels</a>
                    <a href="https://example.com/categ/duelists">Duelists</a>
                </div>
            </div>
            <div>
                <h1>Items<h1>
                <div>
                    <a href="https://example.com/p?id=reyna">Reyna</a>
                    <a href="https://example.com/p?id=jett">Jett</a>
                </div>
                <span>
                    <a href="https://example.com/page-2">Next Page</a>
                </span>
            </div>
            <a href="https://example.com/categ/probably">category??</a>
            <footer>
                <a href="https://example.com/privacy-policy">Privacy Policy</a>
                <a href="https://another-example.com">Link to other domain</a>
            </footer>
        </body>
        </html>
    """
    response = AnyResponse(HttpResponse("https://example.com", body))
    navigation = ProductNavigation.from_dict(
        {
            "url": "https://example.com",
            "subCategories": [
                {"url": "https://example.com/categ/sentinels", "name": "Sentinels"},
                {"url": "https://example.com/categ/duelists", "name": "Duelists"},
            ],
            "items": [
                {"url": "https://example.com/p?id=reyna", "name": "Reyna"},
                {"url": "https://example.com/p?id=jett", "name": "Jett"},
            ],
            "nextPage": {
                "url": "https://example.com/page-2",
                "name": "Next Page",
            },
            "metadata": {"dateDownloaded": "2024-01-09T14:37:58Z"},
        }
    )
    all_valid_urls = [
        "https://example.com/categ/sentinels",
        "https://example.com/categ/duelists",
        "https://example.com/p?id=reyna",
        "https://example.com/p?id=jett",
        "https://example.com/page-2",
    ]
    urls_subcategories = [
        ProbabilityRequest.from_dict(
            {"url": "https://example.com/categ/sentinels", "name": "Sentinels"}
        ),
        ProbabilityRequest.from_dict(
            {"url": "https://example.com/categ/duelists", "name": "Duelists"}
        ),
    ]

    # Heuristics turned OFF
    request_url = RequestUrl(response.url)
    page_params = PageParams({"allow_domains": "example.com"})
    page = HeuristicsProductNavigationPage(
        request_url, navigation, response, page_params
    )
    item = await page.to_item()

    assert item.subCategories == urls_subcategories
    assert page._urls_for_category() == all_valid_urls

    # Heuristics turned ON
    page_params = PageParams({"full_domain": "example.com"})
    page = HeuristicsProductNavigationPage(
        request_url, navigation, response, page_params
    )
    item = await page.to_item()

    assert item.subCategories == urls_subcategories + [
        ProbabilityRequest.from_dict(
            {
                "url": "https://example.com/categ/probably",
                "name": "[heuristics] category??",
                "metadata": {"probability": 0.1},
            }
        )
    ]
    assert page._urls_for_category() == all_valid_urls


@ensureDeferred
async def test_crawl_nofollow_links():
    page_params = PageParams({"full_domain": "example.com"})
    body = b"""
            <html>
            <body>
                <div>
                    <a href="https://outside-example.com/can-follow">Outside link</a>
                    <a href="https://example.com/can-follow">Can follow</a>
                    <a href="https://example.com/dont-follow" rel="nofollow">Dont follow</a>
                </div>
            </body>
            </html>
        """
    url = "https://example.com"
    response = AnyResponse(HttpResponse(url, body))
    request_url = RequestUrl(response.url)
    navigation = ProductNavigation(url=url)

    page = HeuristicsProductNavigationPage(
        request_url, navigation, response, page_params
    )
    assert [req.url for req in page.subCategories] == ["https://example.com/can-follow"]


@pytest.mark.deprication_warning
def test_deprecated_page_objects():
    with pytest.warns(DeprecationWarning, match="page_objects"):
        from zyte_spider_templates.page_objects import (  # noqa: F401
            HeuristicsProductNavigationPage,
        )

    # We cannot test the warning again because duplicate warnings are ignored,
    # but we still want to ensure that we can import the class.
    from zyte_spider_templates.page_objects.product_navigation_heuristics import (  # noqa: F401, F811
        HeuristicsProductNavigationPage,
    )
