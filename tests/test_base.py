import scrapy
from zyte_common_items import ProbabilityRequest, Request

from zyte_spider_templates.spiders.base import BaseSpider


def test_get_subcategory_request():
    url = "https://example.com"

    # Normal request but with mostly empty values

    request = Request(url)
    spider = BaseSpider("")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation

    scrapy_request = spider.get_subcategory_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 0
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "",
            "probability": None,
            "page_type": "subCategories",
        },
    }

    # Non-Heuristics request

    request = ProbabilityRequest.from_dict(
        {"url": url, "name": "Some request", "metadata": {"probability": 0.98}}
    )
    spider = BaseSpider("")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation
    page_params = {"full_domain": "example.com"}

    scrapy_request = spider.get_subcategory_request(request, page_params=page_params)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 98
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "Some request",
            "probability": 0.98,
            "page_type": "subCategories",
        },
    }

    # Heuristics request

    request = ProbabilityRequest.from_dict(
        {
            "url": url,
            "name": "[heuristics] Some request",
            "metadata": {"probability": 0.1},
        }
    )
    spider = BaseSpider("")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation
    page_params = {"full_domain": "example.com"}

    scrapy_request = spider.get_subcategory_request(request, page_params=page_params)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 10
    assert scrapy_request.meta == {
        "page_params": page_params,
        "crawling_logs": {
            "name": "Some request",
            "probability": 0.1,
            "page_type": "productNavigation-heuristics",
        },
    }


def test_get_nextpage_request():
    url = "https://example.com"

    # Minimal Args

    request = Request(url)
    spider = BaseSpider("")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation

    scrapy_request = spider.get_nextpage_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 100
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {"name": "", "probability": None, "page_type": "nextPage"},
    }


def test_get_parse_navigation_request():
    url = "https://example.com"

    # Minimal args

    request = Request(url)
    spider = BaseSpider("")
    parse_navigation = lambda _: None
    spider.parse_navigation = parse_navigation

    scrapy_request = spider.get_parse_navigation_request(request)
    assert isinstance(scrapy_request, scrapy.Request)
    assert scrapy_request.callback == parse_navigation
    assert scrapy_request.priority == 0
    assert scrapy_request.meta == {
        "page_params": {},
        "crawling_logs": {
            "name": "",
            "probability": None,
            "page_type": "productNavigation",
        },
    }
