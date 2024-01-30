import re

from scrapy.utils.url import parse_url


def get_domain(url: str) -> str:
    return re.sub(r"^www\d*\.", "", parse_url(url).netloc)
