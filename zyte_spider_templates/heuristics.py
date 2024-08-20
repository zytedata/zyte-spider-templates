import re
from urllib.parse import urlparse, urlsplit

from zyte_spider_templates._geolocations import GEOLOCATION_OPTIONS
from zyte_spider_templates._lang_codes import LANG_CODES as _LANG_CODES

COUNTRY_CODES = set([k.lower() for k in GEOLOCATION_OPTIONS])
LANG_CODES = set(_LANG_CODES)


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


INDEX_URL_PATHS = {
    "",
    "/index",
    "/index.html",
    "/index.htm",
    "/index.php",
    "/home",
}


def is_homepage(url: str) -> bool:
    """Given a URL, returns True if the URL could be a homepage."""
    url_split = urlsplit(url)
    url_path = url_split.path.rstrip("/").lower()

    # Finds and removes URL subpaths like "/us/en", "en-us", "en-uk", etc.
    if _url_has_locale_pair(url_path):
        url_path = url_path[6:]

    # Finds and removes URL subpaths like "/en", "/fr", etc.
    match = re.search(r"/(\w{2})(?!\w)", url_path)
    if match and (match.group(1) in LANG_CODES or match.group(1) in COUNTRY_CODES):
        url_path = url_path[3:]

    if url_path in INDEX_URL_PATHS and not url_split.query:
        return True

    return False


def _url_has_locale_pair(url_path: str) -> bool:
    if match := re.search(r"/(\w{2})[^a-z](\w{2})(?!\w)", url_path):
        x, y = match.groups()
        if x in LANG_CODES and y in COUNTRY_CODES:
            return True
        if y in LANG_CODES and x in COUNTRY_CODES:
            return True
    return False
