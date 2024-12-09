import pytest
from scrapy.link import Link
from web_poet import BrowserHtml, BrowserResponse, ResponseUrl

from zyte_spider_templates.heuristics import (
    classify_article_crawling_links,
    classify_article_feed_links,
    is_comments_article_feed,
    is_feed_content,
    is_homepage,
    might_be_category,
)


@pytest.mark.parametrize(
    "test_input,expected",
    (
        ("", True),
        ("https://example.com", True),
        ("https://example.com/search", False),
        ("https://example.com/search.php", False),
        ("https://example.com/articles", False),
        ("https://example.com/articles.cgi", False),
        ("https://example.com/articles#fragment-here", False),
        ("https://example.com/xyz123/articles?q=1", False),
        ("https://example.com/xyz123/articles/x?q=1", True),
        # Regex
        ("https://example.com/signin", False),
        ("https://example.com/signin.html", False),
        ("https://example.com/sign-in", False),
        ("https://example.com/sign_in", False),
        ("https://example.com/login", False),
        ("https://example.com/login.html", False),
        ("https://example.com/log-in", False),
        ("https://example.com/log_in", False),
        ("https://example.com/logout", False),
        ("https://example.com/logout.html", False),
        ("https://example.com/log-out", False),
        ("https://example.com/log_out", False),
        ("https://example.com/contact-us", False),
        ("https://example.com/contact_us", False),
        ("https://example.com/contactus", False),
        ("https://example.com/contactus.asp", False),
        ("https://example.com/contact", False),
        ("https://example.com/contact.html", False),
        ("https://example.com/lost_password", False),
        ("https://example.com/lost-password", False),
        ("https://example.com/forgot_password", False),
        ("https://example.com/forgot-password", False),
        ("https://example.com/forgot-password.cgi", False),
        ("https://example.com/terms-of-use", False),
        ("https://example.com/terms-of-use.html", False),
        ("https://example.com/terms-of-service", False),
        ("https://example.com/terms-of-conditions", False),
        ("https://example.com/terms_of_use", False),
        ("https://example.com/terms_of_service", False),
        ("https://example.com/terms_of_conditions", False),
        # subdomains
        ("https://blog.example.com", False),
        ("https://admin.example.com", False),
        ("https://cart.example.com", False),
        ("https://news.example.com", False),
        ("https://careers.example.com", False),
    ),
)
def test_might_be_category(test_input, expected):
    assert might_be_category(test_input) == expected


LOCALES = (
    "/us/en",
    "/en/us",
    "/us-en",
    "/us_en",
    "/AT_en",
    "/pt-br",
    "/PT-br",
    "/en-us",
    "/en-AT",
    "/en",
    "/uk",
)


@pytest.mark.parametrize(
    "url_path,expected",
    (
        ("", True),
        ("/", True),
        ("/index", True),
        ("/index.htm", True),
        ("/index.html", True),
        ("/index.php", True),
        ("/home", True),
        ("/home/", True),
        ("?ref=abc", False),
        ("/some/category", False),
        ("/some/category?query=2123", False),
    ),
)
@pytest.mark.parametrize("locale", LOCALES)
def test_is_homepage(locale, url_path, expected):
    assert is_homepage("https://example.com" + url_path) == expected
    assert is_homepage("https://example.com" + locale + url_path) == expected


@pytest.mark.parametrize(
    "url",
    (
        "https://example.com/zz/dd",
        "https://example.com/dd/zz",
        "https://example.com/dd-zz",
        "https://example.com/dd_zz",
        "https://example.com/DD_zz",
        "https://example.com/bb-DD",
        "https://example.com/DD-BB",
        "https://example.com/dd-zz",
        "https://example.com/dd-ZZ",
        "https://example.com/dd",
        "https://example.com/zz",
    ),
)
def test_is_homepage_localization_bad(url):
    """If the url locale pattern doesn't match the country and language codes,
    then it should not be identified as homepage.
    """
    assert not is_homepage(url)
    assert not is_homepage(url + "/")


@pytest.mark.parametrize(
    "url, expected_result",
    [
        ("http://example.com/comments/feed", True),
        ("http://example.com/?feed=comments-rss2", True),
        ("http://example.com/article/comments/feed", True),
        ("http://example.com/article/?feed=comments-rss2", True),
        ("http://example.com/feed", False),
        ("http://example.com/?feed=rss2", False),
        ("http://example.com/article/feed", False),
        ("http://example.com/article/?feed=rss2", False),
    ],
)
def test_is_comments_article_feed(url, expected_result):
    assert is_comments_article_feed(url) == expected_result


@pytest.mark.parametrize(
    "links, expected_allowed_urls, expected_disallowed_urls",
    [
        (
            [
                Link(url="http://example.com/article1", text="Article 1"),
                Link(url="http://example.com/image.jpg", text="Image"),
                Link(url="http://example.com/page.html", text="Page"),
                Link(url="http://example.com/search", text="Search Page"),
                Link(url="http://t.co", text="Social Media"),
            ],
            ["http://example.com/article1", "http://example.com/page.html"],
            [
                "http://example.com/image.jpg",
                "http://t.co",
                "http://example.com/search",
            ],
        )
    ],
)
def test_classify_article_crawling_links(
    links, expected_allowed_urls, expected_disallowed_urls
):
    allowed_links, disallowed_links = classify_article_crawling_links(links)

    assert len(allowed_links) == len(expected_allowed_urls)
    assert len(disallowed_links) == len(expected_disallowed_urls)

    for url in expected_allowed_urls:
        assert any(link.url == url for link in allowed_links)

    for url in expected_disallowed_urls:
        assert any(link.url == url for link in disallowed_links)


@pytest.mark.parametrize(
    "links, expected_allowed_urls, expected_disallowed_urls",
    [
        (
            [
                Link(url="http://example.com/article1", text="Article 1"),
                Link(url="http://example.com/feed/rss.xml", text="RSS Feed"),
                Link(url="http://example.com/feed/atom.xml", text="Atom Feed"),
                Link(url="http://example.com/comments/feed", text="Comments Feed"),
                Link(url="http://example.com/page.html", text="Page"),
            ],
            [
                "http://example.com/article1",
                "http://example.com/feed/rss.xml",
                "http://example.com/feed/atom.xml",
                "http://example.com/page.html",
            ],
            ["http://example.com/comments/feed"],
        )
    ],
)
def test_classify_article_feed_links(
    links, expected_allowed_urls, expected_disallowed_urls
):
    allowed_links, disallowed_links = classify_article_feed_links(links)

    assert len(allowed_links) == len(expected_allowed_urls)
    assert len(disallowed_links) == len(expected_disallowed_urls)

    assert set(link.url for link in allowed_links) == set(expected_allowed_urls)
    assert set(link.url for link in disallowed_links) == set(expected_disallowed_urls)


def test_is_feed_content_rss():
    rss_content = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
          <channel>
            <title>Example Feed</title>
            <link>http://example.com/</link>
            <description>Example feed description</description>
            <item>
              <title>Example entry</title>
              <link>http://example.com/entry</link>
              <description>Example entry description</description>
            </item>
          </channel>
        </rss>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(rss_content)
        )
    )

    empty_rss_content = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
          <channel>
            <title></title>
            <link></link>
            <description></description>
          </channel>
        </rss>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(empty_rss_content)
        )
    )

    wrong_rss_content = rss_content.replace("channel", "some_channel")
    assert not is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(wrong_rss_content)
        )
    )


def test_is_feed_content_rdf():
    rdf_content = """<?xml version="1.0" encoding="UTF-8" ?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns="http://purl.org/rss/1.0/">
          <channel rdf:about="http://example.com/">
            <title>Example Feed</title>
            <link>http://example.com/</link>
            <description>Example feed description</description>
            <items>
              <rdf:Seq>
                <rdf:li rdf:resource="http://example.com/entry"/>
              </rdf:Seq>
            </items>
          </channel>

          <item rdf:about="http://example.com/entry">
            <title>Example entry</title>
            <link>http://example.com/entry</link>
            <description>Example entry description</description>
          </item>
        </rdf:RDF>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(rdf_content)
        )
    )

    empty_rdf_content = """<?xml version="1.0" encoding="UTF-8" ?>
        <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                 xmlns="http://purl.org/rss/1.0/">
          <channel rdf:about="">
            <title></title>
            <link></link>
            <description></description>
          </channel>
        </rdf:RDF>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(empty_rdf_content)
        )
    )

    wrong_rdf_content = rdf_content.replace("channel", "some_channel")
    assert not is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(wrong_rdf_content)
        )
    )


def test_is_feed_content_atom():
    atom_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title>Example Feed</title>
          <link href="http://example.com/"/>
          <updated>2024-08-01T00:00:00Z</updated>
          <author>
            <name>John Doe</name>
          </author>
          <id>urn:uuid:60a76c80-d399-11d9-b93C-0003939e0af6</id>
          <entry>
            <title>Example entry</title>
            <link href="http://example.com/entry"/>
            <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
            <updated>2024-08-01T00:00:00Z</updated>
            <summary>Example entry description</summary>
          </entry>
        </feed>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(atom_content)
        )
    )

    empty_atom_content = """<?xml version="1.0" encoding="UTF-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <title></title>
          <link href="" />
          <updated></updated>
          <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
        </feed>"""
    assert is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(empty_atom_content)
        )
    )

    wrong_atom_content = atom_content.replace("id", "some_id")
    assert not is_feed_content(
        BrowserResponse(
            ResponseUrl("https://www.example.com"), BrowserHtml(wrong_atom_content)
        )
    )
