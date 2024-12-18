import re
from typing import List, Tuple
from urllib.parse import urlparse, urlsplit

from scrapy.link import Link
from scrapy.linkextractors import IGNORED_EXTENSIONS
from web_poet import BrowserResponse

from zyte_spider_templates._geolocations import GEOLOCATION_OPTIONS
from zyte_spider_templates._lang_codes import LANG_CODES as _LANG_CODES

COUNTRY_CODES = set([k.lower() for k in GEOLOCATION_OPTIONS])
LANG_CODES = set(_LANG_CODES)

ATOM_PATTERN = re.compile(r"<feed[^>]*>.*?<id[^>]*>.*?</id>", re.IGNORECASE | re.DOTALL)
RDF_PATTERN = re.compile(r"<rdf[^>]*>\s*<channel[^>]*>", re.IGNORECASE)
RSS_PATTERN = re.compile(r"<rss[^>]*>\s*<channel[^>]*>", re.IGNORECASE)


NO_CONTENT_KEYWORDS = (
    "authenticate",
    "my-account",
    "account",
    "my-wishlist",
    "search",
    "archive",
    "privacy-policy",
    "cookie-policy",
    "terms-conditions",
    "tos",
    "admin",
    "rss.xml",
    "subscribe",
    "newsletter",
    "settings",
    "cart",
    "articles",
    "artykuly",  # Polish for articles
    "news",
    "blog",
    "about",
    "about-us",
    "affiliate",
    "press",
    "careers",
)

SUFFIXES = [".html", ".php", ".cgi", ".asp"]

NO_CONTENT_RE = (
    r"/sign[_-]?in",
    r"/log[_-]?(in|out)",
    r"/contact[_-]?(us)?",
    r"/(lost|forgot)[_-]password",
    r"/terms[_-]of[_-](service|use|conditions)",
)

NO_ARTICLES_CONTENT_PATHS = (
    "/archive",
    "/about",
    "/about-us",
    "/account",
    "/admin",
    "/affiliate",
    "/authenticate",
    "/best-deals",
    "/careers",
    "/cart",
    "/checkout",
    "/contactez-nous",
    "/cookie-policy",
    "/my-account",
    "/my-wishlist",
    "/press",
    "/pricing",
    "/privacy-policy",
    "/returns",
    "/rss.xml",
    "/search",
    "/settings",
    "/shipping",
    "/subscribe",
    "/terms-conditions",
    "/tos",
)


SEED_URL_RE = re.compile(r"^https?:\/\/[^:\/\s]+(:\d{1,5})?(\/[^\s]*)*(#[^\s]*)?")

NON_HTML_FILE_EXTENSION_RE = re.compile(
    ".*(?:{}$)".format("|".join(re.escape("." + ext) for ext in IGNORED_EXTENSIONS)),
    re.IGNORECASE,
)

SOCIAL_DOMAINS = (
    "facebook.com",
    "youtube.com",
    "youtu.be",
    "twitter.com",
    "t.co",
    "instagram.com",
    "mail.yahoo.com",
    "plus.google.com",
    "play.google.com",
    "www.google.com",
    "itunes.apple.com",
    "login.yahoo.com",
    "consent.yahoo.com",
    "outlook.live.com",
    "linkedin.com",
    "vk.com",
    "www.odnoklassniki.ru",
    "api.whatsapp.com",
    "telegram.me",
    "telegram.org",
    # ads
    "doubleclick.net",
)
domains = "|".join(re.escape(domain) for domain in SOCIAL_DOMAINS)
pattern = rf"(?:^(?:[./])(?:{domains})|\b(?:{domains}))$"
SOCIAL_DOMAINS_RE = re.compile(pattern)


def might_be_category(url: str) -> bool:
    """Returns True if the given url might be a category based on its path."""

    url = url.lower().rstrip("/")
    parsed_url = urlparse(url)

    for suffix in [""] + SUFFIXES:
        for path in NO_CONTENT_KEYWORDS:
            if parsed_url.path.endswith(f"/{path}{suffix}"):
                return False
            if parsed_url.netloc.startswith(f"{path}."):
                return False
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


def is_comments_article_feed(url: str) -> bool:
    """
    Try to guess if a feed URL is for comments, not for articles.
    """
    if "comments/feed" in url or "feed=comments-rss2" in url:
        return True
    return False


def is_non_html_file(url: str) -> bool:
    """
    True for urls with extensions that clearly are not HTML. For example,
    they are images, or a compressed file, etc.
    >>> is_non_html_file("http://example.com/article")
    False
    >>> is_non_html_file("http://example.com/image.jpg")
    True
    """
    return bool(NON_HTML_FILE_EXTENSION_RE.match(url))


def is_social_link(url: str) -> bool:
    """
    True for urls corresponding to the typical social networks
    >>> is_social_link("http://facebook.com")
    True
    >>> is_social_link("http://www.facebook.com")
    True
    >>> is_social_link("http://rrr.t.co")
    True
    >>> is_social_link("http://t.co")
    True
    >>> is_social_link("http://sport.co")
    False
    >>> is_social_link("http://sport.com")
    False
    >>> is_social_link("http://example.com")
    False
    """
    netloc = urlsplit(url).netloc

    if SOCIAL_DOMAINS_RE.search(netloc):
        return True
    return False


def classify_article_crawling_links(links: List[Link]) -> Tuple[List[Link], List[Link]]:
    """In accordance with the rules, it divides the list of links into two new lists with allowed and disallowed links.
    Returns a tuple of these new lists."""
    allowed_links = []
    disallowed_links = []
    for link in links:
        url = link.url
        if (
            is_social_link(url)
            or is_non_html_file(url)
            or url.endswith(NO_ARTICLES_CONTENT_PATHS)
        ):
            disallowed_links.append(link)
            continue
        allowed_links.append(link)

    return allowed_links, disallowed_links


def classify_article_feed_links(links: List[Link]) -> Tuple[List[Link], List[Link]]:
    """In accordance with the rules, it divides the list of urls into two new lists with allowed and disallowed urls.
    Returns a tuple of these new lists."""
    allowed_links = []
    disallowed_links = []
    for link in links:
        if is_comments_article_feed(link.url):
            disallowed_links.append(link)
            continue
        allowed_links.append(link)
    return allowed_links, disallowed_links


def is_feed_content(response: BrowserResponse) -> bool:
    # RSS 0.91, 0.92, 2.0
    if RSS_PATTERN.search(response.html):
        return True
    # Atom feed
    if ATOM_PATTERN.search(response.html):
        return True
    # RSS 1.0/RDF
    if RDF_PATTERN.search(response.html):
        return True
    return False
