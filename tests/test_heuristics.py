import pytest

from zyte_spider_templates.heuristics import is_homepage, might_be_category


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
