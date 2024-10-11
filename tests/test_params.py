import re

import pytest

from zyte_spider_templates.params import URL_FIELD_KWARGS


@pytest.mark.parametrize(
    "valid,url",
    [
        (False, ""),
        (False, "http://"),
        (False, "http:/example.com"),
        (False, "ftp://example.com"),
        (False, "example.com"),
        (False, "//example.com"),
        (False, "http://foo:bar@example.com"),
        (False, " http://example.com"),
        (False, "http://example.com "),
        (False, "http://examp le.com"),
        (False, "https://example.com:232323"),
        (True, "http://example.com"),
        (True, "http://bücher.example"),
        (True, "http://xn--bcher-kva.example"),
        (True, "https://i❤.ws"),
        (True, "https://example.com"),
        (True, "https://example.com/"),
        (True, "https://example.com:2323"),
        (True, "https://example.com:2323/"),
        (True, "https://example.com:2323/foo"),
        (True, "https://example.com/f"),
        (True, "https://example.com/foo"),
        (True, "https://example.com/foo/"),
        (True, "https://example.com/foo/bar"),
        (True, "https://example.com/foo/bar/"),
        (True, "https://example.com/foo/bar?baz"),
        (True, "https://example.com/foo/bar/?baz"),
        (True, "https://example.com?foo"),
        (True, "https://example.com?foo=bar"),
        (True, "https://example.com/?foo=bar&baz"),
        (True, "https://example.com/?foo=bar&baz#"),
        (True, "https://example.com/?foo=bar&baz#frag"),
        (True, "https://example.com#"),
        (True, "https://example.com/#"),
        (True, "https://example.com/&"),
        (True, "https://example.com/&#"),
    ],
)
def test_url_pattern(url, valid):
    assert isinstance(URL_FIELD_KWARGS["pattern"], str)
    assert bool(re.match(URL_FIELD_KWARGS["pattern"], url)) == valid
