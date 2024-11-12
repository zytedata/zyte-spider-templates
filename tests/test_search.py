import pytest
from pytest_twisted import ensureDeferred
from web_poet import AnyResponse, BrowserResponse, HttpResponse, PageParams

from zyte_spider_templates.pages.search_request_template import (
    DefaultSearchRequestTemplatePage,
)


@pytest.mark.parametrize(
    ("html", "page_params", "expected"),
    (
        # Extruct #-----------------------------------------------------------#
        # JSON-LD example from Google
        # https://developers.google.com/search/docs/appearance/structured-data/sitelinks-searchbox#example
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": {
                                "urlTemplate": "https://query.example.com/search?q={search_term_string}"
                            },
                            "query-input": "required name=search_term_string"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Microdata example from Google
        # https://developers.google.com/search/docs/appearance/structured-data/sitelinks-searchbox#example
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="https://query.example.com/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="search_term_string" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Non-compliant JSON-LD that uses a JSON array for potentialAction
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": [
                            {
                                "@type": "SearchAction",
                                "target": {
                                    "urlTemplate": "https://query.example.com/search?q={search_term_string}"
                                },
                                "query-input": "required name=search_term_string"
                            }
                        ]
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Non-default placeholder, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": {
                                "urlTemplate": "https://query.example.com/search?q={q}&dont_replace={search_term_string}"
                            },
                            "query-input": "required name=q"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}&dont_replace={search_term_string}",
            },
        ),
        # Non-default placeholder, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="https://query.example.com/search?q={q}&dont_replace={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="q" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}&dont_replace={search_term_string}",
            },
        ),
        # JSON-LD, WebSite isPartOf WebPage
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebPage",
                        "url": "https://example.com",
                        "isPartOf": {
                            "@type": "WebSite",
                            "@id": "https://example.com/#website",
                            "url": "https://example.com",
                            "potentialAction":
                            {
                                "@type": "SearchAction",
                                "target": "https://query.example.com/search?q={search_term_string}",
                                "query-input": "required name=search_term_string"
                            }
                        },
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Relative URL, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": {
                                "urlTemplate": "/search?q={search_term_string}"
                            },
                            "query-input": "required name=search_term_string"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Relative URL, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="search_term_string" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Wrong escaping in JSON-LD
        (
            rb"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "http:\/\/schema.org",
                        "@type": "WebSite",
                        "url": "https:\/\/example.com\/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": "https:\/\/example.com\/search?a=b&amp;q={q}",
                            "query-input": "required name=q"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://example.com/search?a=b&q={{ query|quote_plus }}",
            },
        ),
        # Query in path, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": {
                                "urlTemplate": "https://example.com/s/{q}"
                            },
                            "query-input": "required name=q"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://example.com/s/{{ query|urlencode }}",
            },
        ),
        # Relative URL, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="https://example.com/s/{q}"/>
                    <input itemprop="query-input" type="text" name="q" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://example.com/s/{{ query|urlencode }}",
            },
        ),
        # No potentialAction, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "error": "Cannot build a search request template",
            },
        ),
        # No potentialAction, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="https://query.example.com/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="search_term_string" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {"error": "Cannot build a search request template"},
        ),
        # No SearchAction type, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "target": {
                                "urlTemplate": "https://query.example.com/search?q={search_term_string}"
                            },
                            "query-input": "required name=search_term_string"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {"error": "Cannot build a search request template"},
        ),
        # No SearchAction type, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope>
                    <meta itemprop="target" content="https://query.example.com/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="search_term_string" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {"error": "Cannot build a search request template"},
        ),
        # No target, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "query-input": "required name=search_term_string"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {"error": "Cannot build a search request template"},
        ),
        # No target, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta content="https://query.example.com/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" name="search_term_string" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {"error": "Cannot build a search request template"},
        ),
        # No query variable name, JSON-LD
        (
            b"""
            <html>
                <head>
                    <title>The title of the page</title>
                    <script type="application/ld+json">
                    {
                        "@context": "https://schema.org",
                        "@type": "WebSite",
                        "url": "https://www.example.com/",
                        "potentialAction": {
                            "@type": "SearchAction",
                            "target": {
                                "urlTemplate": "https://query.example.com/search?q={search_term_string}"
                            },
                            "query-input": "required"
                        }
                    }
                    </script>
                </head>
                <body>
                </body>
            </html>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # No query variable name, Microdata
        (
            b"""
            <div itemscope itemtype="https://schema.org/WebSite">
                <meta itemprop="url" content="https://www.example.com/"/>
                <form itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction">
                    <meta itemprop="target" content="https://query.example.com/search?q={search_term_string}"/>
                    <input itemprop="query-input" type="text" required/>
                    <input type="submit"/>
                </form>
            </div>
            """,
            {"search_request_builders": ["extruct"]},
            {
                "url": "https://query.example.com/search?q={{ query|quote_plus }}",
            },
        ),
        # Formasaurus and form heuristics #-----------------------------------#
        *(
            (html, {"search_request_builders": [builder]}, expected)
            for builder in ("formasaurus", "form_heuristics")
            for html, expected in (
                # Basic form
                (
                    b"""
                    <form class="search">
                        <input type="text" name="q"/>
                        <input type="submit"/>
                    </form>
                    """,
                    {
                        "url": "https://example.com?q={{ query|quote_plus }}",
                    },
                ),
                # No form
                (
                    b"<div></div>",
                    {"error": "Cannot build a search request template"},
                ),
                # No named input field
                (
                    b"""
                    <form class="search">
                        <input type="submit"/>
                    </form>
                    """,
                    {"error": "Cannot build a search request template"},
                ),
                # Multi-part form
                (
                    b"""
                    <form class="search" enctype="multipart/form-data" method="post">
                        <input type="text" name="q"/>
                        <input type="submit"/>
                    </form>
                    """,
                    {"error": "Cannot build a search request template"},
                ),
                # Non-HTML response (JSON)
                (
                    b"""{"a": "b"}""",
                    {"error": "Cannot build a search request template"},
                ),
            )
        ),
        # Link heuristics #---------------------------------------------------#
        # Link with recognized parameters
        *(
            (
                f"""<a href="https://example.com/search?{prefix}{q}=example{suffix}""".encode(),
                {"search_request_builders": ["link_heuristics"]},
                {
                    "url": f"https://example.com/search?{prefix}{q}={{{{ query|quote_plus }}}}{suffix}"
                },
            )
            for q in (
                "q",
                "query",
                "s",
                "search",
                "searchquery",
                "search_query",
                "search-query",
                "searchQuery",
                "SearchQuery",
                "pSearchQuery",
                "term",
                "text",
            )
            for prefix in ("", "a=b&")
            for suffix in ("", "&c=d")
        ),
        # No link
        (
            b"""<div></div>""",
            {"search_request_builders": ["link_heuristics"]},
            {"error": "Cannot build a search request template"},
        ),
        # No HTML (JSON)
        (
            b"""{"a": "b"}""",
            {"search_request_builders": ["link_heuristics"]},
            {"error": "Cannot build a search request template"},
        ),
        # Parameter false positive (?q != q)
        (
            b"""<a href="https://example.com?a=b&?q=c"></a>""",
            {"search_request_builders": ["link_heuristics"]},
            {"error": "Cannot build a search request template"},
        ),
        # Builder parameters #------------------------------------------------#
        *(
            (
                b"""
                    <div itemscope itemtype="https://schema.org/WebSite">
                        <meta itemprop="url" content="https://www.example.com/"/>
                        <form action="/form" itemprop="potentialAction" itemscope itemtype="https://schema.org/SearchAction" class="search">
                            <meta itemprop="target" content="https://example.com/metadata?q={q}"/>
                            <input itemprop="query-input" type="text" name="q" required/>
                            <input type="submit"/>
                        </form>
                    </div>
                """,
                page_params,
                expected,
            )
            for page_params, expected in (
                # By default, the popular builder strategy is used, meaning
                # that even though the Extruct builder has the highest
                # priority, if both the Formasaurus builder and the form
                # heuristics builder output the same URL, that one is used
                # instead.
                ({}, {"url": "https://example.com/form?q={{ query|quote_plus }}"}),
                (
                    {"search_request_builder_strategy": "popular"},
                    {"url": "https://example.com/form?q={{ query|quote_plus }}"},
                ),
                (
                    {"search_request_builder_strategy": "first"},
                    {"url": "https://example.com/metadata?q={{ query|quote_plus }}"},
                ),
                # Strategies only take into account the specified builders, and
                # in the supplied order.
                (
                    {
                        "search_request_builder_strategy": "first",
                        "search_request_builders": ["formasaurus", "extruct"],
                    },
                    {"url": "https://example.com/form?q={{ query|quote_plus }}"},
                ),
                (
                    {
                        "search_request_builder_strategy": "popular",
                        "search_request_builders": [
                            "extruct",
                            "formasaurus",
                            "link_heuristics",
                        ],
                    },
                    {"url": "https://example.com/metadata?q={{ query|quote_plus }}"},
                ),
                # Unsupported strategies trigger a ValueError
                (
                    {"search_request_builder_strategy": "unsupported"},
                    ValueError(
                        "Unsupported search_request_builder_strategy value: 'unsupported'"
                    ),
                ),
            )
        ),
    ),
)
@ensureDeferred
async def test_search_request_template(html, page_params, expected, caplog):
    caplog.clear()
    caplog.at_level("ERROR")

    http_response = HttpResponse(url="https://example.com", status=200, body=html)
    response = AnyResponse(response=http_response)
    search_request_page = DefaultSearchRequestTemplatePage(
        response=response,
        page_params=PageParams(**page_params),
    )
    try:
        search_request = await search_request_page.to_item()
    except Exception as exception:
        assert isinstance(expected, Exception)
        assert exception.__class__ == expected.__class__
        assert str(expected) in str(exception)
    else:
        if "error" in expected:
            probability = search_request.get_probability()
            assert probability is not None
            assert probability <= 0.0
            assert expected["error"] in caplog.text
        else:
            assert isinstance(expected, dict)
            assert expected["url"] == search_request.url
            assert expected.get("body", b"") == (search_request.body or b"")


@ensureDeferred
async def test_search_request_template_browser(caplog):
    """Do not suggest using a browser request if that is already the case."""
    caplog.clear()
    caplog.at_level("ERROR")

    browser_response = BrowserResponse(
        url="https://example.com", status=200, html="<div></div>"
    )
    response = AnyResponse(response=browser_response)
    search_request_page = DefaultSearchRequestTemplatePage(
        response=response, page_params=PageParams()
    )
    item = await search_request_page.to_item()
    probability = item.get_probability()
    assert probability is not None
    assert probability <= 0.0
    assert "A quick workaround would be to use" in caplog.text
