import pytest

from zyte_spider_templates.utils import get_domain, load_url_list

URL_TO_DOMAIN = (
    ("https://example.com", "example.com"),
    ("https://www.example.com", "example.com"),
    ("https://www2.example.com", "example.com"),
    ("https://prefixwww.example.com", "prefixwww.example.com"),
    ("https://wwworld.example.com", "wwworld.example.com"),
    ("https://my.wwworld-example.com", "my.wwworld-example.com"),
    ("https://wwwow.com", "wwwow.com"),
    ("https://wowww.com", "wowww.com"),
    ("https://awww.com", "awww.com"),
)


@pytest.mark.parametrize("url,domain", URL_TO_DOMAIN)
def test_get_domain(url, domain):
    assert get_domain(url) == domain


@pytest.mark.parametrize(
    "input_urls,expected",
    (
        (
            "https://a.example",
            ["https://a.example"],
        ),
        (
            "   https://a.example    ",
            ["https://a.example"],
        ),
        (
            "https://a.example\n \nhttps://b.example\nhttps://c.example\n\n",
            ["https://a.example", "https://b.example", "https://c.example"],
        ),
        (
            "ftp://a.example",
            ValueError,
        ),
    ),
)
def test_load_url_list(input_urls, expected):
    if isinstance(expected, list):
        assert load_url_list(input_urls) == expected
        return
    with pytest.raises(expected):
        load_url_list(input_urls)
