import pytest

from zyte_spider_templates import BaseSpiderParams


def test_deprecation():
    with pytest.deprecated_call(match="^BaseSpiderParams is deprecated.*"):
        BaseSpiderParams(url="https://example.com")  # type: ignore[call-arg]
