import logging
import os
from unittest.mock import patch

import pytest
from scrapy import Request, Spider

from tests import get_crawler
from zyte_spider_templates.utils import (
    get_domain,
    get_domain_fingerprint,
    get_project_id,
    get_request_fingerprint,
    get_spider_name,
    load_url_list,
)

URL_TO_DOMAIN = (
    ("https://example.com", "example.com"),
    ("https://www.example.com", "example.com"),
    ("https://www2.example.com", "example.com"),
    ("https://prefixwww.example.com", "prefixwww.example.com"),
    ("https://wwworld.example.com", "wwworld.example.com"),
    ("https://my.wwworld-example.com", "my.wwworld-example.com"),
    ("https://wwwow.com", "wwwow.com"),
    ("https://wowww.com", "wowww.com"),
    ("https://awww.com", "awww.com"),
)


@pytest.mark.parametrize("url,domain", URL_TO_DOMAIN)
def test_get_domain(url, domain):
    assert get_domain(url) == domain


@pytest.mark.parametrize(
    "input_urls,expected",
    (
        (
            "https://a.example",
            ["https://a.example"],
        ),
        (
            "   https://a.example    ",
            ["https://a.example"],
        ),
        (
            "https://a.example\n \nhttps://b.example\nhttps://c.example\n\n",
            ["https://a.example", "https://b.example", "https://c.example"],
        ),
        (
            "ftp://a.example",
            ValueError,
        ),
    ),
)
def test_load_url_list(input_urls, expected):
    if isinstance(expected, list):
        assert load_url_list(input_urls) == expected
        return
    with pytest.raises(expected):
        load_url_list(input_urls)


@pytest.mark.parametrize(
    "url, expected_fingerprint",
    [
        # No subdomain
        ("https://example.com", "c300"),
        # One subdomain
        ("https://sub.example.com", "c35d"),
        # Multiple subdomains
        ("https://sub1.sub2.example.com", "c3c9"),
        # No TLD (localhost or internal addresses)
        ("http://localhost", "3300"),
        # Complex TLD (e.g., .co.uk) and subdomains
        ("https://sub.example.co.uk", "c35d"),
    ],
)
def test_get_domain_fingerprint(url, expected_fingerprint):
    assert get_domain_fingerprint(url) == expected_fingerprint


@pytest.mark.parametrize(
    "env_var_value, spider_name, expected_result, expected_log",
    [
        (
            "virtual_spider_name",
            "regular_spider_name",
            "virtual_spider_name",
            "Picked virtual spider name virtual_spider_name from the spider's SHUB_VIRTUAL_SPIDER setting.",
        ),
        (
            None,
            "regular_spider_name",
            "regular_spider_name",
            "Picked spider name regular_spider_name from the spider.",
        ),
    ],
)
def test_get_spider_name(
    env_var_value, spider_name, expected_result, expected_log, caplog
):
    class TestSpider(Spider):
        name = spider_name

    caplog.clear()
    crawler = get_crawler()
    crawler.spider = TestSpider()

    logger = logging.getLogger("zyte_spider_templates.utils")
    logger.setLevel(logging.INFO)

    with patch.dict(
        os.environ,
        {"SHUB_VIRTUAL_SPIDER": env_var_value} if env_var_value else {},
        clear=True,
    ):
        result = get_spider_name(crawler)
        assert result == expected_result
        assert expected_log in caplog.text


@pytest.mark.parametrize(
    "env_scrapy, env_zyte, settings_zyte, expected_result, expected_log, expect_exception",
    [
        # SCRAPY_PROJECT_ID is set
        (
            "123456",
            None,
            None,
            "123456",
            "Picked project id 123456 from SCRAPY_PROJECT_ID env variable.",
            False,
        ),
        # ZYTE_PROJECT_ID is set in the environment
        (
            None,
            "654321",
            None,
            "654321",
            "Picked project id 654321 from ZYTE_PROJECT_ID env variable.",
            False,
        ),
        # ZYTE_PROJECT_ID is set in the settings
        (
            None,
            None,
            "126534",
            "126534",
            "Picked project id 126534 from the spider's ZYTE_PROJECT_ID setting.",
            False,
        ),
        # No project ID found, expect an exception
        (
            None,
            None,
            None,
            None,  # No result expected
            None,  # No log expected
            True,  # Expect an exception
        ),
    ],
)
def test_get_project_id(
    env_scrapy,
    env_zyte,
    settings_zyte,
    expected_result,
    expected_log,
    expect_exception,
    caplog,
):
    caplog.clear()

    env_vars = {}
    if env_scrapy:
        env_vars["SCRAPY_PROJECT_ID"] = env_scrapy
    if env_zyte:
        env_vars["ZYTE_PROJECT_ID"] = env_zyte

    with patch.dict(os.environ, env_vars, clear=True):
        crawler = get_crawler()

        if settings_zyte:
            crawler.settings.set("ZYTE_PROJECT_ID", settings_zyte)

        with caplog.at_level(logging.INFO, logger="zyte_spider_templates.utils"):
            if expect_exception:
                with pytest.raises(
                    ValueError,
                    match="Zyte project id wasn't found in job data, env, or settings.",
                ):
                    get_project_id(crawler)
            else:
                assert get_project_id(crawler) == expected_result
                assert expected_log in caplog.text


def test_get_request_fingerprint():
    url = "https://example.com"
    domain_fp = "ffeeddccbbaa"
    request_fp = "aabbccddeeff"

    with patch(
        "zyte_spider_templates.utils.get_domain_fingerprint", return_value=domain_fp
    ):
        crawler = get_crawler()
        with patch.object(crawler, "request_fingerprinter") as mock_fingerprinter:
            mock_fingerprinter.fingerprint.return_value = bytes.fromhex(request_fp)
            request = Request(url)
            result = get_request_fingerprint(crawler, request)
            assert result == domain_fp + request_fp
            mock_fingerprinter.fingerprint.assert_called_once_with(request)
