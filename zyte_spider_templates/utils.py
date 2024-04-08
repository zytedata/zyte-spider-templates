import re
from typing import List

from scrapy.utils.url import parse_url

_URL_PATTERN = r"^https?://[^:/\s]+(:\d{1,5})?(/[^\s]*)*(#[^\s]*)?$"


def get_domain(url: str) -> str:
    return re.sub(r"^www\d*\.", "", parse_url(url).netloc)


def load_url_list(urls: str) -> List[str]:
    result = []
    bad_urls = []
    for url in urls.split("\n"):
        if not (url := url.strip()):
            continue
        if not re.search(_URL_PATTERN, url):
            bad_urls.append(url)
        elif not bad_urls:
            result.append(url)
    if bad_urls:
        bad_url_list = "\n".join(bad_urls)
        raise ValueError(
            f"URL list contained the following invalid URLs:\n{bad_url_list}"
        )
    return result
