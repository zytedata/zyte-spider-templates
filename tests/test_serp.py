import pytest
from pydantic import ValidationError
from scrapy_spider_metadata import get_spider_metadata

from zyte_spider_templates.spiders.serp import GoogleSearchSpider

from . import get_crawler
from .utils import assertEqualSpiderMetadata


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
                    "title": "Max Pages",
                    "type": "integer",
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
