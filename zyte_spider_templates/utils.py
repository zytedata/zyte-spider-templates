import re
from typing import List

from scrapy.utils.url import parse_url


def get_domain(url: str) -> str:
    return re.sub(r"^www\d*\.", "", parse_url(url).netloc)


def load_url_list(urls: str) -> List[str]:
    urls = [url.strip() for url in urls.split("\n")]
    return [url for url in urls if url]
