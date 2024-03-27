import re
from urllib.parse import urlparse


class ContentFilter:
    def __init__(self, no_content_paths, no_content_regex, suffixes=None):
        self.no_content_paths = no_content_paths
        self.no_content_regex = no_content_regex
        self.suffixes = (
            suffixes if suffixes is not None else [".html", ".php", ".cgi", ".asp"]
        )

    def might_be_relevant_content(self, url: str) -> bool:
        """Returns True if the given URL might be relevant based on its path and predefined rules."""
        url = url.lower().rstrip("/")
        url_path = urlparse(url).path

        for suffix in [""] + self.suffixes:
            for path in self.no_content_paths:
                if url_path.endswith(path + suffix):
                    return False
            for rule in self.no_content_regex:
                if re.search(rule + suffix, url):
                    return False

        return True


product_filter = ContentFilter(
    no_content_paths=(
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
    ),
    no_content_regex=(
        r"/sign[_-]?in",
        r"/log[_-]?(in|out)",
        r"/contact[_-]?(us)?",
        r"/(lost|forgot)[_-]password",
        r"/terms[_-]of[_-](service|use|conditions)",
    ),
)

article_filter = ContentFilter(
    no_content_paths=(
        "/authenticate",
        "/my-account",
        "/account",
        "/my-wishlist",
        "/cart",
        "/checkout",
        "/order",
        "/shop",
        "/product",
        "/products",
        "/category",
        "/categories",
        "/privacy-policy",
        "/cookie-policy",
        "/terms-conditions",
        "/tos",
        "/admin",
        "/login",
        "/signup",
        "/subscribe",
        "/newsletter",
        "/settings",
        "/faq",
        "/help",
        "/support",
        "/downloads",
        "/careers",
        "/jobs",
        "/contact",
        "/about",
        "/about-us",
        "/team",
        "/testimonials",
        "/reviews",
    ),
    no_content_regex=(
        r"/sign[_-]?in",
        r"/log[_-]?(in|out)",
        r"/contact[_-]?(us)?",
        r"/(lost|forgot)[_-]password",
        r"/terms[_-]of[_-](service|use|conditions)",
    ),
)
