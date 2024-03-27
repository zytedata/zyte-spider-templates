import pytest
from pytest_twisted import ensureDeferred
from web_poet import AnyResponse, HttpResponse, PageParams, RequestUrl
from zyte_common_items import ArticleNavigation, ProbabilityRequest

from zyte_spider_templates.pages.article_navigation_heuristics import (
    HeuristicsArticleNavigationPage,
)


@ensureDeferred
async def test_unknown_article_page():
    body = b"""
        <html>
        <body>
            <div>
                <h1>Categories</h1>
                <div>
                    <a href="https://example.com/category/news">News</a>
                    <a href="https://example.com/category/sports">Sports</a>
                </div>
            </div>
            <div>
                <h1>Articles</h1>
                <div>
                    <a href="https://example.com/article?id=breaking-news">Breaking News</a>
                    <a href="https://example.com/article?id=latest-scores">Latest Scores</a>
                </div>
                <span>
                    <a href="https://example.com/page-2">Next Page</a>
                </span>
            </div>
            <a href="https://example.com/category/probably-relevant">Probably Relevant?</a>
            <footer>
                <a href="https://example.com/privacy-policy">Privacy Policy</a>
                <a href="https://another-example.com">Link to other domain</a>
            </footer>
        </body>
        </html>
    """
    response = AnyResponse(HttpResponse("https://example.com", body))
    navigation = ArticleNavigation.from_dict(
        {
            "url": "https://example.com",
            "subCategories": [
                {"url": "https://example.com/category/news", "name": "News"},
                {"url": "https://example.com/category/sports", "name": "Sports"},
            ],
            "items": [
                {
                    "url": "https://example.com/article?id=breaking-news",
                    "name": "Breaking News",
                },
                {
                    "url": "https://example.com/article?id=latest-scores",
                    "name": "Latest Scores",
                },
            ],
            "nextPage": {
                "url": "https://example.com/page-2",
                "name": "Next Page",
            },
            "metadata": {"dateDownloaded": "2024-01-09T14:37:58Z"},
        }
    )
    all_valid_urls = [
        "https://example.com/category/news",
        "https://example.com/category/sports",
        "https://example.com/article?id=breaking-news",
        "https://example.com/article?id=latest-scores",
        "https://example.com/page-2",
    ]
    urls_subcategories = [
        ProbabilityRequest.from_dict(
            {"url": "https://example.com/category/news", "name": "News"}
        ),
        ProbabilityRequest.from_dict(
            {"url": "https://example.com/category/sports", "name": "Sports"}
        ),
    ]

    # Heuristics turned OFF
    request_url = RequestUrl(response.url)
    page_params = PageParams({"allow_domains": "example.com"})
    page = HeuristicsArticleNavigationPage(
        request_url, navigation, response, page_params
    )
    item = await page.to_item()

    assert item.subCategories == urls_subcategories
    assert page._urls_for_navigation() == all_valid_urls

    # Heuristics turned ON
    page_params = PageParams({"full_domain": "example.com"})
    page = HeuristicsArticleNavigationPage(
        request_url, navigation, response, page_params
    )
    item = await page.to_item()

    assert item.subCategories == urls_subcategories + [
        ProbabilityRequest.from_dict(
            {
                "url": "https://example.com/category/probably-relevant",
                "name": "[heuristics] Probably Relevant?",
                "metadata": {"probability": 0.1},
            }
        )
    ]
    assert page._urls_for_navigation() == all_valid_urls


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
    navigation = ArticleNavigation(url=url)

    page = HeuristicsArticleNavigationPage(
        request_url, navigation, response, page_params
    )
    assert [req.url for req in page.subCategories] == ["https://example.com/can-follow"]


def test_deprecated_page_objects():
    with pytest.warns(DeprecationWarning, match="page_objects"):
        from zyte_spider_templates.page_objects import (  # noqa: F401
            HeuristicsArticleNavigationPage,
        )

    # We cannot test the warning again because duplicate warnings are ignored,
    # but we still want to ensure that we can import the class.
    from zyte_spider_templates.page_objects.article_navigation_heuristics import (  # noqa: F401, F811
        HeuristicsArticleNavigationPage,
    )
