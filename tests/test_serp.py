from urllib.parse import quote_plus

import pytest
from scrapy import Request
from scrapy_spider_metadata import get_spider_metadata
from scrapy_zyte_api.responses import ZyteAPITextResponse
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Product

from zyte_spider_templates._geolocations import (
    GEOLOCATION_OPTIONS,
    GEOLOCATION_OPTIONS_WITH_CODE,
    Geolocation,
)
from zyte_spider_templates.spiders._google_gl import (
    GOOGLE_GL_OPTIONS,
    GOOGLE_GL_OPTIONS_WITH_CODE,
    GoogleGl,
)
from zyte_spider_templates.spiders._google_hl import (
    GOOGLE_HL_OPTIONS,
    GOOGLE_HL_OPTIONS_WITH_CODE,
    GoogleHl,
)
from zyte_spider_templates.spiders.serp import (
    ITEM_TYPE_CLASSES,
    GoogleSearchSpider,
    SerpItemType,
)

from . import get_crawler
from .utils import assertEqualSpiderMetadata


def run_parse_serp(spider, total_results=99999, page=1, query="foo", results=10):
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
                    for rank in range(1, results + 1)
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
                "max_requests": {
                    "anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}],
                    "default": 100,
                    "description": (
                        "The maximum number of Zyte API requests allowed for the crawl.\n"
                        "\n"
                        "Requests with error responses that cannot be retried or exceed "
                        "their retry limit also count here, but they incur in no costs "
                        "and do not increase the request count in Scrapy Cloud."
                    ),
                    "title": "Max Requests",
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
                "results_per_page": {
                    "anyOf": [
                        {
                            "minimum": 1,
                            "type": "integer",
                        },
                        {
                            "type": "null",
                        },
                    ],
                    "default": None,
                    "description": "Maximum number of results per page.",
                    "title": "Results Per Page",
                },
                "item_type": {
                    "default": "off",
                    "description": (
                        "If specified, follow organic search result links, "
                        "and extract the selected data type from the target "
                        "pages. Spider output items will be of the specified "
                        "data type, not search engine results page items."
                    ),
                    "enum": [
                        "off",
                        "article",
                        "articleList",
                        "forumThread",
                        "jobPosting",
                        "product",
                        "productList",
                    ],
                    "title": "Follow and Extract",
                    "type": "string",
                },
                "gl": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "Boosts results relevant to this country. See "
                        "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.gl"
                    ),
                    "enumMeta": {
                        code: {
                            "title": GOOGLE_GL_OPTIONS_WITH_CODE[code],
                        }
                        for code in sorted(GoogleGl)
                    },
                    "title": "User Country (gl)",
                    "enum": list(
                        sorted(GOOGLE_GL_OPTIONS, key=GOOGLE_GL_OPTIONS.__getitem__)
                    ),
                },
                "cr": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "Restricts search results to documents originating in "
                        "particular countries. See "
                        "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.cr"
                    ),
                    "title": "Content Countries (cr)",
                },
                "geolocation": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": "Country of the IP addresses to use.",
                    "enumMeta": {
                        code: {
                            "title": GEOLOCATION_OPTIONS_WITH_CODE[code],
                        }
                        for code in sorted(Geolocation)
                    },
                    "title": "IP Country",
                    "enum": list(
                        sorted(GEOLOCATION_OPTIONS, key=GEOLOCATION_OPTIONS.__getitem__)
                    ),
                },
                "hl": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "User interface language, which can affect search "
                        "results. See "
                        "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.hl"
                    ),
                    "enumMeta": {
                        code: {
                            "title": GOOGLE_HL_OPTIONS_WITH_CODE[code],
                        }
                        for code in sorted(GoogleHl)
                    },
                    "title": "User Language (hl)",
                    "enum": list(
                        sorted(GOOGLE_HL_OPTIONS, key=GOOGLE_HL_OPTIONS.__getitem__)
                    ),
                },
                "lr": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "null"},
                    ],
                    "default": None,
                    "description": (
                        "Restricts search results to documents written in the "
                        "specified languages. See "
                        "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.lr"
                    ),
                    "title": "Content Languages (lr)",
                },
            },
            "required": ["search_queries"],
            "title": "GoogleSearchSpiderParams",
            "type": "object",
        },
    }
    assertEqualSpiderMetadata(actual_metadata, expected_metadata)

    geolocation = actual_metadata["param_schema"]["properties"]["geolocation"]
    assert geolocation["enum"][0] == "AF"
    assert geolocation["enumMeta"]["UY"] == {"title": "Uruguay (UY)"}
    assert set(geolocation["enum"]) == set(geolocation["enumMeta"])


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
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo bar", max_pages=3
    )

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

    items, requests = run_parse_serp(
        spider,
        total_results=None,
    )
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=10"
    assert requests[0].cb_kwargs["page_number"] == 2

    # Ensure a lack of results stops pagination even if total_results reports
    # additional results.
    # https://github.com/zytedata/zyte-spider-templates/pull/80/files/359c342008e2e4d5a913d450ddd2dda6c887747c#r1840897802
    items, requests = run_parse_serp(
        spider,
        total_results=None,
        results=0,
    )
    assert len(items) == 1
    assert len(requests) == 0

    # Do not go over max_pages
    items, requests = run_parse_serp(
        spider,
        total_results=31,
        page=3,
    )
    assert len(items) == 1
    assert len(requests) == 0


def test_get_serp_request():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(crawler, search_queries="foo bar")
    url = "https://www.google.com/search?q=foo+bar"

    request = spider.get_serp_request(url, page_number=42)
    assert request.cb_kwargs["page_number"] == 42

    # The page_number parameter is required.
    with pytest.raises(TypeError):
        spider.get_serp_request(url)  # type: ignore[call-arg]


def test_parse_serp():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo bar", max_pages=43
    )
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
        spider.parse_serp(response)  # type: ignore[call-arg]


def test_hl():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo", hl="gl", max_pages=2
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&hl=gl"

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=10&hl=gl"


def test_lr():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo", lr="lang_ja", max_pages=2
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&lr=lang_ja"

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=10&lr=lang_ja"


def test_cr():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo", cr="(-countryFR).(-countryIT)", max_pages=2
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert (
        requests[0].url
        == "https://www.google.com/search?q=foo&cr=%28-countryFR%29.%28-countryIT%29"
    )

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert (
        requests[0].url
        == "https://www.google.com/search?q=foo&start=10&cr=%28-countryFR%29.%28-countryIT%29"
    )


def test_gl():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo", gl="af", max_pages=2
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&gl=af"

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=10&gl=af"


def test_results_per_page():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo", results_per_page=1, max_pages=2
    )
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&num=1"

    items, requests = run_parse_serp(spider)
    assert len(items) == 1
    assert len(requests) == 1
    assert requests[0].url == "https://www.google.com/search?q=foo&start=1&num=1"


def test_item_type():
    crawler = get_crawler()
    spider = GoogleSearchSpider.from_crawler(
        crawler, search_queries="foo bar", max_pages=43, item_type="product"
    )
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
    assert len(items) == 0
    assert len(requests) == 11

    assert requests[0].url == add_or_replace_parameter(url, "start", "420")
    assert requests[0].cb_kwargs["page_number"] == 43

    for rank in range(1, 11):
        assert requests[rank].url == f"https://example.com/{rank}"
        assert requests[rank].callback == spider.parse_result
        assert requests[rank].meta == {
            "crawling_logs": {"page_type": "product"},
            "inject": [Product],
        }


def test_item_type_mappings():
    # Ensure that all SerpItemType keys and values match.
    for entry in SerpItemType:
        assert entry.name == entry.value

    # Ensure that the ITEM_TYPE_CLASSES dict maps all values from the
    # corresponding enum except for serp.
    actual_keys = set(ITEM_TYPE_CLASSES)
    expected_keys = set(
        entry.value for entry in SerpItemType if entry != SerpItemType.off
    )
    assert actual_keys == expected_keys

    # Also ensure that no dict value is repeated.
    assert len(actual_keys) == len(set(ITEM_TYPE_CLASSES.values()))
