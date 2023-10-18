import re
from urllib.parse import urlparse

NO_CONTENT_PATHS = (
    "/authenticate",
    "/my-account",
    "/account",
    "/my-wishlist",
    "/search",
    "/archive",
    "/privacy-policy",
    "/cookie-policy",
    "/terms-conditions",
    "/tos",
    "/admin",
    "/rss.xml",
    "/subscribe",
    "/newsletter",
    "/settings",
    "/cart",
    "/articles",
    "/artykuly",  # Polish for articles
    "/news",
    "/blog",
    "/about",
    "/about-us",
    "/affiliate",
    "/press",
    "/careers",
)

SUFFIXES = [".html", ".php", ".cgi", ".asp"]

NO_CONTENT_RE = (
    r"/sign[_-]?in",
    r"/log[_-]?(in|out)",
    r"/contact[_-]?(us)?",
    r"/(lost|forgot)[_-]password",
    r"/terms[_-]of[_-](service|use|conditions)",
)


def might_be_category(url: str) -> bool:
    """Returns True if the given url might be a category based on its path."""

    url = url.lower().rstrip("/")
    url_path = urlparse(url).path

    for suffix in [""] + SUFFIXES:
        for path in NO_CONTENT_PATHS:
            if url_path.endswith(path + suffix):
                return False
    for suffix in [""] + SUFFIXES:
        for rule in NO_CONTENT_RE:
            if re.search(rule + suffix, url):
                return False

    return True
