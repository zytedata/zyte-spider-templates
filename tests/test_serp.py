from urllib.parse import quote_plus

import pytest
from pydantic import ValidationError
from scrapy import Request
from scrapy_spider_metadata import get_spider_metadata
from scrapy_zyte_api.responses import ZyteAPITextResponse
from w3lib.url import add_or_replace_parameter

from zyte_spider_templates.spiders._google_hl import (
    GOOGLE_HL_OPTIONS,
    GOOGLE_HL_OPTIONS_WITH_CODE,
    GoogleHl,
)
from zyte_spider_templates.spiders.serp import GoogleSearchSpider

from . import get_crawler
from .utils import assertEqualSpiderMetadata


def run_parse_serp(spider, total_results=99999, page=1, query="foo"):
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    if page > 1:
        url = add_or_replace_parameter(url, "start", (page - 1) * 10)
    response = ZyteAPITextResponse.from_api_response(
        api_response={
            "serp": {
                "organicResults": [
                    {
                        "description": "…",
                        "name": "…",
                        "url": f"https://example.com/{rank}",
                        "rank": rank,
                    }
                    for rank in range(1, 11)
                ],
                "metadata": {
                    "dateDownloaded": "2024-10-25T08:59:45Z",
                    "displayedQuery": query,
                    "searchedQuery": query,
                    "totalOrganicResults": total_results,
                },
                "pageNumber": page,
                "url": url,
            },
            "url": url,
        },
    )
    items = []
    requests = []
    for item_or_request in spider.parse_serp(response, page_number=page):
        if isinstance(item_or_request, Request):
            requests.append(item_or_request)
        else:
            items.append(item_or_request)
    return items, requests


def test_parameters():
    with pytest.raises(ValidationError):
        GoogleSearchSpider()

    with pytest.raises(ValidationError):
        GoogleSearchSpider(domain="google.com")

    GoogleSearchSpider(search_queries="foo bar")
    GoogleSearchSpider(domain="google.cat", search_queries="foo bar")
    GoogleSearchSpider(domain="google.cat", search_queries="foo bar", max_pages=10)

    with pytest.raises(ValidationError):
        GoogleSearchSpider(domain="google.foo", search_queries="foo bar")

    with pytest.raises(ValidationError):
        GoogleSearchSpider(search_queries="foo bar", max_pages="all")


def test_start_requests():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar")
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo+bar"
    assert requests[0].callback == spider.parse_serp


def test_metadata():
    actual_metadata = get_spider_metadata(GoogleSearchSpider, normalize=True)
    expected_metadata = {
        "template": True,
        "title": "Google Search Results",
        "description": "Template for spiders that extract Google search results.",
        "param_schema": {
            "properties": {
                "domain": {
                    "default": "google.com",
                    "description": "Target Google domain.",
                    "title": "Domain",
                    "enum": [
                        "google.com",
                        "google.ad",
                        "google.ae",
                        "google.al",
                        "google.am",
                        "google.as",
                        "google.at",
                        "google.az",
                        "google.ba",
                        "google.be",
                        "google.bf",
                        "google.bg",
                        "google.bi",
                        "google.bj",
                        "google.bs",
                        "google.bt",
                        "google.by",
                        "google.ca",
                        "google.cat",
                        "google.cd",
                        "google.cf",
                        "google.cg",
                        "google.ch",
                        "google.ci",
                        "google.cl",
                        "google.cm",
                        "google.cn",
                        "google.co.ao",
                        "google.co.bw",
                        "google.co.ck",
                        "google.co.cr",
                        "google.co.id",
                        "google.co.il",
                        "google.co.in",
                        "google.co.jp",
                        "google.co.ke",
                        "google.co.kr",
                        "google.co.ls",
                        "google.co.ma",
                        "google.co.mz",
                        "google.co.nz",
                        "google.co.th",
                        "google.co.tz",
                        "google.co.ug",
                        "google.co.uk",
                        "google.co.uz",
                        "google.co.ve",
                        "google.co.vi",
                        "google.co.za",
                        "google.co.zm",
                        "google.co.zw",
                        "google.com.af",
                        "google.com.ag",
                        "google.com.ar",
                        "google.com.au",
                        "google.com.bd",
                        "google.com.bh",
                        "google.com.bn",
                        "google.com.bo",
                        "google.com.br",
                        "google.com.bz",
                        "google.com.co",
                        "google.com.cu",
                        "google.com.cy",
                        "google.com.do",
                        "google.com.ec",
                        "google.com.eg",
                        "google.com.et",
                        "google.com.fj",
                        "google.com.gh",
                        "google.com.gi",
                        "google.com.gt",
                        "google.com.hk",
                        "google.com.jm",
                        "google.com.kh",
                        "google.com.kw",
                        "google.com.lb",
                        "google.com.ly",
                        "google.com.mm",
                        "google.com.mt",
                        "google.com.mx",
                        "google.com.my",
                        "google.com.na",
                        "google.com.ng",
                        "google.com.ni",
                        "google.com.np",
                        "google.com.om",
                        "google.com.pa",
                        "google.com.pe",
                        "google.com.pg",
                        "google.com.ph",
                        "google.com.pk",
                        "google.com.pr",
                        "google.com.py",
                        "google.com.qa",
                        "google.com.sa",
                        "google.com.sb",
                        "google.com.sg",
                        "google.com.sl",
                        "google.com.sv",
                        "google.com.tj",
                        "google.com.tr",
                        "google.com.tw",
                        "google.com.ua",
                        "google.com.uy",
                        "google.com.vc",
                        "google.com.vn",
                        "google.cv",
                        "google.cz",
                        "google.de",
                        "google.dj",
                        "google.dk",
                        "google.dm",
                        "google.dz",
                        "google.ee",
                        "google.es",
                        "google.fi",
                        "google.fm",
                        "google.fr",
                        "google.ga",
                        "google.ge",
                        "google.gg",
                        "google.gl",
                        "google.gm",
                        "google.gr",
                        "google.gy",
                        "google.hn",
                        "google.hr",
                        "google.ht",
                        "google.hu",
                        "google.ie",
                        "google.im",
                        "google.iq",
                        "google.is",
                        "google.it",
                        "google.je",
                        "google.jo",
                        "google.kg",
                        "google.ki",
                        "google.kz",
                        "google.la",
                        "google.li",
                        "google.lk",
                        "google.lt",
                        "google.lu",
                        "google.lv",
                        "google.md",
                        "google.me",
                        "google.mg",
                        "google.mk",
                        "google.ml",
                        "google.mn",
                        "google.mu",
                        "google.mv",
                        "google.mw",
                        "google.ne",
                        "google.nl",
                        "google.no",
                        "google.nr",
                        "google.nu",
                        "google.pl",
                        "google.pn",
                        "google.ps",
                        "google.pt",
                        "google.ro",
                        "google.rs",
                        "google.ru",
                        "google.rw",
                        "google.sc",
                        "google.se",
                        "google.sh",
                        "google.si",
                        "google.sk",
                        "google.sm",
                        "google.sn",
                        "google.so",
                        "google.sr",
                        "google.st",
                        "google.td",
                        "google.tg",
                        "google.tl",
                        "google.tm",
                        "google.tn",
                        "google.to",
                        "google.tt",
                        "google.vu",
                        "google.ws",
                    ],
                    "type": "string",
                },
                "search_queries": {
                    "anyOf": [
                        {"items": {"type": "string"}, "type": "array"},
                        {"type": "null"},
                    ],
                    "description": "Input 1 search query per line (e.g. foo bar).",
                    "title": "Search Queries",
                    "widget": "textarea",
                },
                "max_pages": {
                    "default": 1,
                    "description": (
                        "Maximum number of result pages to visit per search query."
                    ),
                    "minimum": 1,
                    "title": "Max Pages",
                    "type": "integer",
                },
                "hl": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "Set the Google user interface language, which "
                        "can affect search results."
                    ),
                    "enumMeta": {
                        code: {
                            "title": GOOGLE_HL_OPTIONS_WITH_CODE[code],
                        }
                        for code in sorted(GoogleHl)
                    },
                    "title": "UI Language",
                    "enum": list(
                        sorted(GOOGLE_HL_OPTIONS, key=GOOGLE_HL_OPTIONS.__getitem__)
                    ),
                },
                "max_requests": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": 100,
                    "description": (
                        "The maximum number of Zyte API requests allowed for the crawl.\n"
                        "\n"
                        "Requests with error responses that cannot be retried or exceed "
                        "their retry limit also count here, but they incur in no costs "
                        "and do not increase the request count in Scrapy Cloud."
                    ),
                    "title": "Max Requests",
                    "widget": "request-limit",
                },
            },
            "required": ["search_queries"],
            "title": "GoogleSearchSpiderParams",
            "type": "object",
        },
    }
    assertEqualSpiderMetadata(actual_metadata, expected_metadata)


def test_input_none():
    crawler = get_crawler()
    with pytest.raises(ValueError):
        GoogleSearchSpider.from_crawler(crawler)


@pytest.mark.parametrize(
    ("input_domain", "expected_domain"),
    (
        (None, "google.com"),
        ("google.com", "google.com"),
        ("google.cat", "google.cat"),
    ),
)
def test_domain(input_domain, expected_domain):
    crawler = get_crawler()
    kwargs = {}
    if input_domain:
        kwargs["domain"] = input_domain
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo bar", **kwargs
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == f"https://www.{expected_domain}/search?q=foo+bar"


def test_search_queries():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar\nbaz")
    requests = list(spider.start_requests())
    assert len(requests) == 2
    assert requests[0].url == "https://www.google.com/search?q=foo+bar"
    assert requests[1].url == "https://www.google.com/search?q=baz"


def test_pagination():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar")

    items, requests = run_parse_serp(
        spider,
        total_results=10,
    )
    assert len(items) == 1
    assert len(requests) == 0

    items, requests = run_parse_serp(
        spider,
        total_results=11,
        query="foo bar",
    )
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo+bar&start=10"
    assert requests[0].cb_kwargs["page_number"] == 2

    items, requests = run_parse_serp(
        spider,
        total_results=20,
        page=2,
        query="foo bar",
    )
    assert len(items) == 1
    assert len(requests) == 0

    items, requests = run_parse_serp(
        spider,
        total_results=21,
        page=2,
        query="foo bar",
    )
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo+bar&start=20"
    assert requests[0].cb_kwargs["page_number"] == 3


def test_get_serp_request():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar")
    url = "https://www.google.com/search?q=foo+bar"

    request = spider.get_serp_request(url, page_number=42)
    assert request.cb_kwargs["page_number"] == 42

    # The page_number parameter is required.
    with pytest.raises(TypeError):
        spider.get_serp_request(url)


def test_parse_serp():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar")
    url = "https://www.google.com/search?q=foo+bar"
    response = ZyteAPITextResponse.from_api_response(
        api_response={
            "serp": {
                "organicResults": [
                    {
                        "description": "…",
                        "name": "…",
                        "url": f"https://example.com/{rank}",
                        "rank": rank,
                    }
                    for rank in range(1, 11)
                ],
                "metadata": {
                    "dateDownloaded": "2024-10-25T08:59:45Z",
                    "displayedQuery": "foo bar",
                    "searchedQuery": "foo bar",
                    "totalOrganicResults": 99999,
                },
                "pageNumber": 1,
                "url": url,
            },
            "url": url,
        },
    )
    items = []
    requests = []
    for item_or_request in spider.parse_serp(response, page_number=42):
        if isinstance(item_or_request, Request):
            requests.append(item_or_request)
        else:
            items.append(item_or_request)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == add_or_replace_parameter(url, "start", "420")
    assert requests[0].cb_kwargs["page_number"] == 43

    # The page_number parameter is required.
    with pytest.raises(TypeError):
        spider.parse_serp(response)


def test_hl():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo", hl="gl")
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&hl=gl"

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=10&hl=gl"
