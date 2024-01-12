import re

from scrapy.utils.url import parse_url


def get_domain(url: str) -> str:
    allowed_domain = parse_url(url).netloc
    allowed_domain = re.sub(r"www.*?\.", "", allowed_domain)
    return allowed_domain
