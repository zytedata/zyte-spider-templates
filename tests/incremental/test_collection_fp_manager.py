from asyncio import ensure_future
from unittest.mock import MagicMock, patch

import pytest
from scrapy import Spider
from scrapy.statscollectors import StatsCollector
from scrapy.utils.request import RequestFingerprinter
from scrapy.utils.test import get_crawler as _get_crawler
from twisted.internet.defer import Deferred, inlineCallbacks

from zyte_spider_templates._incremental.manager import (
    CollectionsFingerprintsManager,
    _get_collection_name,
)
from zyte_spider_templates.spiders.article import ArticleSpider

from .. import get_crawler, set_env


@pytest.fixture
def mock_crawler():
    return MagicMock()


def crawler_for_incremental():
    url = "https://example.com"
    crawler = get_crawler()
    crawler.request_fingerprinter = RequestFingerprinter()
    crawler.stats = StatsCollector(crawler)
    crawler.spider = ArticleSpider.from_crawler(crawler, url=url)
    crawler.settings["ZYTE_PROJECT_ID"] = "000000"
    return crawler


@pytest.mark.parametrize("batch_size", [50, 2])
@pytest.mark.parametrize(
    "fingerprints, keys_in_collection, fingerprints_batch, expected_result",
    [
        ([], [], {"fp1", "fp2", "fp3"}, set()),
        (["fp1", "fp2", "fp3"], [], set(), set()),
        (["fp1", "fp2", "fp3"], ["fp1"], set(), {"fp1"}),
        (["fp1", "fp2", "fp3"], ["fp1", "fp2"], set(), {"fp1", "fp2"}),
        (["fp1", "fp2", "fp3"], ["fp1", "fp2", "fp3"], set(), {"fp1", "fp2", "fp3"}),
        (
            ["fp1", "fp2", "fp3"],
            ["fp1", "fp2"],
            {("fp3", "url3")},
            {"fp1", "fp2", "fp3"},
        ),
        (["fp1", "fp2", "fp3"], [], {("fp3", "url3")}, {"fp3"}),
    ],
)
@patch("scrapinghub.ScrapinghubClient")
@inlineCallbacks
def test_get_existing_fingerprints(
    mock_scrapinghub_client,
    batch_size,
    fingerprints,
    keys_in_collection,
    fingerprints_batch,
    expected_result,
):
    mock_client = MagicMock()
    mock_scrapinghub_client.return_value = mock_client

    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_client.get_project.return_value.collections.get_store.return_value = (
        mock_collection
    )

    mock_crawler = MagicMock()
    mock_crawler.settings.getint.return_value = batch_size

    mock_manager = CollectionsFingerprintsManager(mock_crawler)
    mock_manager.get_keys_from_collection = MagicMock(return_value=keys_in_collection)  # type: ignore
    mock_manager.batch = fingerprints_batch

    r = yield Deferred.fromFuture(
        ensure_future(mock_manager.get_existing_fingerprints_async(fingerprints))
    )
    assert r == expected_result


@pytest.mark.parametrize(
    "fingerprints, expected_keys",
    [
        ({"fp1", "fp2", "fp3"}, {"fp1", "fp2", "fp3"}),
        ({}, set()),
    ],
)
@patch("scrapinghub.ScrapinghubClient")
def test_get_keys_from_collection(mock_crawler, fingerprints, expected_keys):
    mock_collection = MagicMock()
    mock_collection.list.return_value = [
        {"_key": key, "value": {}} for key in expected_keys
    ]
    mock_crawler.settings.getint.return_value = 50
    manager = CollectionsFingerprintsManager(mock_crawler)
    manager.collection = mock_collection  # type: ignore
    assert manager.get_keys_from_collection(fingerprints) == expected_keys


@pytest.mark.parametrize(
    "keys, expected_items_written",
    [
        (
            [("fp1", "url1"), ("fp2", "url2"), ("fp3", "url3")],
            [("fp1", "url1"), ("fp2", "url2"), ("fp3", "url3")],
        ),
        ([], []),
    ],
)
@patch("scrapinghub.ScrapinghubClient")
def test_save_to_collection(mock_crawler, keys, expected_items_written):
    mock_writer = MagicMock()
    mock_writer.write.return_value = expected_items_written
    mock_crawler.settings.getint.return_value = 50
    manager = CollectionsFingerprintsManager(mock_crawler)
    manager.writer = mock_writer  # type: ignore
    manager.save_to_collection(keys)
    mock_writer.write.assert_called_once_with(
        [{"_key": key, "value": value} for key, value in keys]
    )


@pytest.mark.parametrize(
    "fingerprints, expected_batch, batch_size",
    [
        (
            [(f"fp{i}", f"url{i}") for i in range(1, 5)],
            {("fp4", "url4")},
            3,
        ),  # No default min
        ([], set(), 20),
        ([("fp1", "url1")] * 19, {("fp1", "url1")}, 20),
        (
            [(f"fp{i}", f"url{i}") for i in range(1, 103)],
            {(f"fp{i}", f"url{i}") for i in range(1, 103)},
            150,
        ),  # No default max
        (
            [(f"fp{i}", f"url{i}") for i in range(1, 53)],
            [("fp51", "url51"), ("fp52", "url52")],
            0,
        ),  # 50 by default
    ],
)
@patch("scrapinghub.ScrapinghubClient")
def test_save_fingerprints(
    mock_scrapinghub_client, fingerprints, expected_batch, batch_size
):
    crawler = crawler_for_incremental()
    if batch_size != 0:
        crawler.settings.set("INCREMENTAL_CRAWL_BATCH_SIZE", batch_size)
    fp_manager = CollectionsFingerprintsManager(crawler)
    fp_manager.save_batch = MagicMock(side_effect=fp_manager.save_batch)  # type: ignore
    fp_manager.add_to_batch(fingerprints)
    assert fp_manager.batch == set(sorted(expected_batch, key=lambda x: int(x[0][2:])))

    if len(fingerprints) >= fp_manager.batch_size:
        fp_manager.save_batch.assert_called_once()
    else:
        fp_manager.save_batch.assert_not_called()


@pytest.mark.parametrize(
    "fingerprints_batch, expected_batch_size",
    [
        ([], 0),
        ([("fp1", "url1"), ("fp2", "url2"), ("fp3", "url3")], 0),
    ],
)
@patch("scrapinghub.ScrapinghubClient")
def test_save_batch(mock_crawler, fingerprints_batch, expected_batch_size):
    crawler = crawler_for_incremental()
    fp_manager = CollectionsFingerprintsManager(crawler)
    fp_manager.batch = set(fingerprints_batch)
    fp_manager.save_batch()
    assert len(fp_manager.batch) == expected_batch_size


@pytest.mark.parametrize(
    "project_id, collection_name, expected_collection",
    [
        ("project1", "collection1", MagicMock()),
        ("project2", "collection2", MagicMock()),
    ],
)
@patch("scrapinghub.ScrapinghubClient")
def test_init_collection(
    mock_scrapinghub_client,
    mock_crawler,
    project_id,
    collection_name,
    expected_collection,
):
    mock_scrapinghub_instance = MagicMock()
    mock_get_project = MagicMock()
    mock_get_project.collections.get_store.return_value = expected_collection
    mock_scrapinghub_instance.get_project.return_value = mock_get_project
    mock_scrapinghub_client.return_value = mock_scrapinghub_instance
    mock_crawler.settings.getint.return_value = 50
    manager = CollectionsFingerprintsManager(mock_crawler)
    manager.init_collection(project_id, collection_name)
    assert manager.collection == expected_collection


@patch("scrapinghub.ScrapinghubClient")
def test_spider_closed(mock_scrapinghub_client):
    crawler = crawler_for_incremental()
    fp_manager = CollectionsFingerprintsManager(crawler)
    fp_manager.save_batch = MagicMock(side_effect=fp_manager.save_batch)  # type: ignore
    fp_manager.spider_closed()
    fp_manager.save_batch.assert_called_once()


@pytest.mark.parametrize(
    ("env_vars", "settings", "spider_name", "collection_name"),
    (
        # INCREMENTAL_CRAWL_COLLECTION_NAME > SHUB_VIRTUAL_SPIDER > Spider.name
        # INCREMENTAL_CRAWL_COLLECTION_NAME is used as is, others are
        # slugified, length-limited and they and get an “_incremental” suffix.
        (
            {},
            {},
            "a A-1.α" + "a" * 2048,
            "a_A_1__" + "a" * (2048 - len("a_A_1_a_incremental")) + "_incremental",
        ),
        (
            {"SHUB_VIRTUAL_SPIDER": "a A-1.α" + "a" * 2048},
            {},
            "foo",
            "a_A_1__" + "a" * (2048 - len("a_A_1_a_incremental")) + "_incremental",
        ),
        (
            {"SHUB_VIRTUAL_SPIDER": "bar"},
            {"INCREMENTAL_CRAWL_COLLECTION_NAME": "a A-1.α" + "a" * 2048},
            "foo",
            "a A-1.α" + "a" * 2048,
        ),
    ),
)
def test_collection_name(env_vars, settings, spider_name, collection_name):
    class TestSpider(Spider):
        name = spider_name

    crawler = _get_crawler(settings_dict=settings, spidercls=TestSpider)
    crawler.spider = TestSpider()
    with set_env(**env_vars):
        assert _get_collection_name(crawler) == collection_name
