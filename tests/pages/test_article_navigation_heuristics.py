from unittest.mock import patch

from pytest_twisted import ensureDeferred
from web_poet import (
    AnyResponse,
    HttpResponse,
    HttpResponseHeaders,
    PageParams,
    RequestUrl,
    Stats,
)
from zyte_common_items import ProbabilityMetadata, ProbabilityRequest

from zyte_spider_templates.pages.article_heuristics import (
    HeuristicsArticleNavigationPage,
)


@ensureDeferred
async def test_article_page():
    body = b"""
        <html>
        <body>
            <div>
                <h1>Categories<h1>
                <div>
                    <a href="https://example.com/category/UX">UX</a>
                    <a href="https://example.com/category/CSS">CSS</a>
                </div>
            </div>
            <div>
                <h1>Articles<h2>
                <div>
                    <a href="https://example.com/2024/05/modern-css">Modern CSS</a>
                    <a href="https://example.com/2024/04/how-run-ux">How to run UX</a>
                </div>
                <span>
                    <a href="https://example.com/page-2">Next Page</a>
                </span>
            </div>
            <footer>
                <a href="https://example.com/privacy-policy">Privacy Policy</a>
                <a href="https://another-example.com">Link to other domain</a>
                <a href="https://example.com/feed/rss.xml">RSS feed</a>
            </footer>
        </body>
        </html>
    """
    response = AnyResponse(HttpResponse("https://example.com", body))

    rss_content = b"""
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
    </channel>
    </rss>
    """
    rss_response = AnyResponse(
        HttpResponse(
            "https://example.com/feed/rss.xml",
            rss_content,
            headers=HttpResponseHeaders({"Content-Type": "text/xml"}),
        )
    )

    urls_subcategories = [
        {"url": "https://example.com/category/UX", "name": "UX"},
        {"url": "https://example.com/category/CSS", "name": "CSS"},
        {"url": "https://example.com/2024/05/modern-css", "name": "Modern CSS"},
        {"url": "https://example.com/2024/04/how-run-ux", "name": "How to run UX"},
        {"url": "https://example.com/page-2", "name": "Next Page"},
        {"url": "https://another-example.com", "name": "Link to other domain"},
    ]
    requests_subcategories = [
        ProbabilityRequest(
            url=subcat["url"],
            name=f"[heuristics][articleNavigation][subCategories] {subcat['name']}",
            headers=None,
            metadata=ProbabilityMetadata(probability=0.5),
        )
        for subcat in urls_subcategories
    ]

    urls_feed = [
        {"url": "https://example.com/feed/rss.xml"},
    ]
    requests_feed = [
        ProbabilityRequest(
            url=feed["url"],
            name="[heuristics][articleNavigation][feed] ",
            headers=None,
            metadata=ProbabilityMetadata(probability=1.0),
        )
        for feed in urls_feed
    ]

    feed_items = ["http://example.com/item1", "http://example.com/item2"]

    urls_items = [
        {"url": "https://example.com/category/UX", "name": "UX"},
        {"url": "https://example.com/category/CSS", "name": "CSS"},
        {"url": "https://example.com/2024/05/modern-css", "name": "Modern CSS"},
        {"url": "https://example.com/2024/04/how-run-ux", "name": "How to run UX"},
        {"url": "https://example.com/page-2", "name": "Next Page"},
        {"url": "https://another-example.com", "name": "Link to other domain"},
    ]
    requests_items = [
        ProbabilityRequest(
            url=item["url"],
            name=f"[heuristics][articleNavigation][article] {item['name']}",
            headers=None,
            metadata=ProbabilityMetadata(probability=0.5),
        )
        for item in urls_items
    ]

    request_url = RequestUrl(response.url)
    rss_url = RequestUrl(rss_response.url)

    # final_navigation_page = True
    page_params = PageParams({"skip_subcategories": True})
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert page.skip_subcategories()
    assert item.subCategories[0].url == "https://example.com/feed/rss.xml"
    assert [item.url for item in item.items] == [item["url"] for item in urls_items]

    # final_navigation_page = False
    page_params = PageParams({"skip_subcategories": False})
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert not page.skip_subcategories()
    assert item.subCategories == requests_feed + requests_subcategories
    assert item.items == requests_items

    # no final_navigation_page (False by default)
    page_params = PageParams()
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert not page.skip_subcategories()
    assert item.subCategories == requests_feed + requests_subcategories
    assert item.items == requests_items

    # only_feeds = True, request to page
    page_params = PageParams({"only_feeds": True})
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert page.is_only_feeds()
    assert item.subCategories[0].url == str(rss_url)
    assert [item.url for item in item.items] == []

    # only_feeds = True, request to feed
    page = HeuristicsArticleNavigationPage(rss_url, rss_response, Stats(), page_params)
    with patch.object(
        HeuristicsArticleNavigationPage, "_is_response_feed", return_value=True
    ):
        item = await page.to_item()
    assert page.is_only_feeds()
    assert item.subCategories == []
    assert [item.url for item in item.items] == feed_items

    # only_feeds = False, request to page
    page_params = PageParams({"only_feeds": False})
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert not page.is_only_feeds()
    assert item.subCategories == requests_feed + requests_subcategories
    assert item.items == requests_items

    # only_feeds = False, request to feed
    page = HeuristicsArticleNavigationPage(rss_url, rss_response, Stats(), page_params)
    with patch.object(
        HeuristicsArticleNavigationPage, "_is_response_feed", return_value=True
    ):
        item = await page.to_item()
    assert not page.is_only_feeds()
    assert item.subCategories == []
    assert [item.url for item in item.items] == feed_items

    # no only_feeds (False by default)
    page_params = PageParams()
    page = HeuristicsArticleNavigationPage(request_url, response, Stats(), page_params)
    item = await page.to_item()

    assert not page.is_only_feeds()
    assert item.subCategories == requests_feed + requests_subcategories
    assert item.items == requests_items

    # no only_feeds (False by default), request to feed
    page = HeuristicsArticleNavigationPage(rss_url, rss_response, Stats(), page_params)
    with patch.object(
        HeuristicsArticleNavigationPage, "_is_response_feed", return_value=True
    ):
        item = await page.to_item()
    assert not page.is_only_feeds()
    assert item.subCategories == []
    assert [item.url for item in item.items] == feed_items
