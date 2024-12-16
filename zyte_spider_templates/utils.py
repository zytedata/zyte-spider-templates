import hashlib
import logging
import os
import re
from typing import List, Optional

import scrapinghub
import tldextract
from scrapy.crawler import Crawler
from scrapy.http import Request
from scrapy.utils.url import parse_url

logger = logging.getLogger(__name__)

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


def get_domain_fingerprint(url: str) -> str:
    """
    Create a consistent 2-byte domain fingerprint by combining partial hashes
    of the main domain (without TLD) and the subdomain components.
    """
    extracted = tldextract.extract(url)
    main_domain = extracted.domain
    subdomains = extracted.subdomain

    # Calculate partial hashes for each component
    main_domain_hash = hashlib.sha1(main_domain.encode("utf-8")).hexdigest()[:2]
    subdomain_hash = (
        hashlib.sha1(subdomains.encode("utf-8")).hexdigest()[:2] if subdomains else "00"
    )

    return main_domain_hash + subdomain_hash


def get_request_fingerprint(crawler: Crawler, request: Request) -> str:
    """Create a fingerprint by including a domain-specific part."""

    # Calculate domain fingerprint
    domain_fingerprint = get_domain_fingerprint(request.url)

    # Calculate request fingerprint
    request_fingerprint = crawler.request_fingerprinter.fingerprint(request).hex()  # type: ignore[union-attr]

    # Combine the fingerprints by taking the 2-bytes (4 chars) domain fingerprint
    # to create a domain-specific identifier.
    # This optimization aids in efficient read/write operations in the Collection.

    return domain_fingerprint + request_fingerprint


def get_project_id(crawler: Crawler) -> Optional[str]:
    """
    Retrieve the project ID required for IncrementalCrawlMiddleware.

    The function attempts to obtain the project ID in the following order:
    1. For Scrapy Cloud deployments, the project ID is automatically set as SCRAPY_PROJECT_ID
       in the environment variables.
    2. Otherwise, it checks the ZYTE_PROJECT_ID environment variable.
    3. If still not found, it checks the spider setting named ZYTE_PROJECT_ID.

    """

    if project_id := os.environ.get("SCRAPY_PROJECT_ID"):
        logger.info(
            f"Picked project id {project_id} from SCRAPY_PROJECT_ID env variable."
        )
        return project_id
    # Try to pick from manually set environmental variable
    if project_id := os.environ.get("ZYTE_PROJECT_ID"):
        logger.info(
            f"Picked project id {project_id} from ZYTE_PROJECT_ID env variable."
        )
        return project_id
    # Try to pick from settings
    if project_id := crawler.settings.get("ZYTE_PROJECT_ID"):
        logger.info(
            f"Picked project id {project_id} from the spider's ZYTE_PROJECT_ID setting."
        )
        return project_id
    raise ValueError(
        "Zyte project id wasn't found in job data, env, or settings. "
        "The env variable SCRAPY_PROJECT_ID or settings property ZYTE_PROJECT_ID was expected."
    )


def get_spider_name(crawler: Crawler) -> str:
    if spider_name := os.environ.get("SHUB_VIRTUAL_SPIDER"):
        logger.info(
            f"Picked virtual spider name {spider_name} from the spider's SHUB_VIRTUAL_SPIDER setting."
        )
        return spider_name

    logger.info(f"Picked spider name {crawler.spider.name} from the spider.")  # type: ignore[union-attr]
    return crawler.spider.name  # type: ignore[union-attr]


def get_client() -> scrapinghub.ScrapinghubClient:
    # auth is taken from SH_APIKEY or SHUB_JOBAUTH
    return scrapinghub.ScrapinghubClient(
        dash_endpoint=os.getenv("SHUB_APIURL"),
        endpoint=os.getenv("SHUB_STORAGE"),
    )
