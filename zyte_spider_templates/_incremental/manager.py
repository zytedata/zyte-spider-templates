import asyncio
import logging
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Set, Tuple, Union

import scrapinghub
from itemadapter import ItemAdapter
from scrapinghub.client.exceptions import Unauthorized
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.http.request import Request
from zyte_common_items import Item

from zyte_spider_templates.utils import (
    get_client,
    get_project_id,
    get_request_fingerprint,
    get_spider_name,
)

logger = logging.getLogger(__name__)

INCREMENTAL_SUFFIX = "_incremental"
COLLECTION_API_URL = "https://storage.scrapinghub.com/collections"

THREAD_POOL_EXECUTOR = ThreadPoolExecutor(max_workers=10)


class CollectionsFingerprintsManager:
    def __init__(self, crawler: Crawler) -> None:
        self.writer = None
        self.collection = None
        self.crawler = crawler

        self.batch: Set[Tuple[str, str]] = set()
        self.batch_size = crawler.settings.getint("INCREMENTAL_CRAWL_BATCH_SIZE", 50)

        project_id = get_project_id(crawler)
        collection_name = self.get_collection_name(crawler)

        self.init_collection(project_id, collection_name)
        self.api_url = f"{COLLECTION_API_URL}/{project_id}/s/{collection_name}"

        logger.info(
            f"Configuration of CollectionsFingerprintsManager for IncrementalCrawlMiddleware:\n"
            f"batch_size: {self.batch_size},\n"
            f"project: {project_id},\n"
            f"collection_name: {collection_name}"
        )

        crawler.signals.connect(self.spider_closed, signal=signals.spider_closed)

    def get_collection_name(self, crawler):
        return (
            crawler.settings.get("INCREMENTAL_CRAWL_COLLECTION_NAME")
            or f"{get_spider_name(crawler)}{INCREMENTAL_SUFFIX}"
        )

    def init_collection(self, project_id, collection_name) -> None:
        client = get_client()
        collection = client.get_project(project_id).collections.get_store(
            collection_name
        )
        try:
            # Trying to get a random key to make sure the collection exists.
            collection.list(key=["init_key"])
        except scrapinghub.client.exceptions.NotFound as e:
            if f"unknown collection {collection_name}" in str(e):
                logger.info(
                    f"The collection: {collection_name} for {project_id=} doesn't exist"
                    f" and will be created automatically"
                )
                # This trick forces the creation of a collection.
                collection.set({"_key": "init", "value": "1"})
                collection.delete("init")
            else:
                logger.error(f"The error {e} for {project_id=}")
                raise RuntimeError("incremental_crawling__not_found_exception")
        except Unauthorized:
            logger.error("The api key (SH_APIKEY or SHUB_JOBAUTH) is not valid.")
            raise ValueError("incremental_crawling__api_key_not_vaild")

        self.collection = collection
        self.writer = self.collection.create_writer()  # type: ignore

    def save_to_collection(self, items_to_save) -> None:
        """Saves the current batch of fingerprints to the collection."""
        items = [{"_key": key, "value": value} for key, value in items_to_save]
        self.writer.write(items)  # type: ignore
        self.writer.flush()  # type: ignore

    async def get_keys_from_collection_async(self, keys: Set[str]) -> Set[str]:
        """Asynchronously fetches a set of keys from the collection using an executor to run in separate threads."""
        return await asyncio.get_event_loop().run_in_executor(
            THREAD_POOL_EXECUTOR, lambda: self.get_keys_from_collection(keys)
        )

    async def read_batches(self, fingerprints: List[str], batch_start: int) -> Set[str]:
        """Reads a specific batch of fingerprints and fetches corresponding keys asynchronously."""
        return await self.get_keys_from_collection_async(
            set(fingerprints[batch_start : batch_start + self.batch_size])
        )

    def get_keys_from_collection(self, keys: Set[str]) -> Set[str]:
        """Synchronously fetches a set of keys from the collection."""
        return {item.get("_key", "") for item in self.collection.list(key=keys)}  # type: ignore

    async def get_existing_fingerprints_async(
        self, fingerprints: List[str]
    ) -> Set[str]:
        """Asynchronously checks for duplicate fingerprints in both the collection and the local buffer.
        Async interaction with the collection could be replaced by
        https://github.com/scrapinghub/python-scrapinghub/issues/169 in the future"""

        fingerprints_size = len(fingerprints)

        if fingerprints_size == 0:
            return set()

        duplicated_fingerprints = set()

        tasks = [
            self.read_batches(fingerprints, i)
            for i in range(0, fingerprints_size, self.batch_size)
        ]
        for future in asyncio.as_completed(tasks):
            try:
                batch_keys = await future
                duplicated_fingerprints.update(batch_keys)
            except Exception as e:
                logging.error(f"Error while processing batch: {e}")

        # Check duplicates in the local buffer
        local_duplicates = set(fingerprints) & {fp for fp, _ in self.batch}
        duplicated_fingerprints.update(local_duplicates)

        return duplicated_fingerprints

    def add_to_batch(self, fp_url_map: Set[Tuple[str, str]]) -> None:
        """
        Add the list of provided fingerprints and corresponding URLs per one item to the batch
        """
        for fp_url in fp_url_map:
            logger.debug(f"Adding fingerprint and URL ({fp_url}) to batch.")
            self.crawler.stats.inc_value(  # type: ignore[union-attr]
                "incremental_crawling/fingerprint_url_to_batch"
            )
            self.batch.add(fp_url)
            if len(self.batch) >= self.batch_size:
                self.save_batch()
        self.crawler.stats.inc_value("incremental_crawling/add_to_batch")  # type: ignore[union-attr]

    def save_batch(self) -> None:
        if not self.batch:
            return
        logger.debug(
            f"Saving {len(self.batch)} fingerprints to the Collection. "
            f"The fingerprints are: {self.batch}."
        )
        self.crawler.stats.inc_value("incremental_crawling/batch_saved")  # type: ignore[union-attr]
        self.save_to_collection(items_to_save=self.batch)
        self.batch.clear()

    def spider_closed(self) -> None:
        """Save fingerprints and corresponding URLs remaining in the batch, before spider closes."""
        self.save_batch()


class IncrementalCrawlingManager:
    def __init__(self, crawler: Crawler, fm: CollectionsFingerprintsManager) -> None:
        self.crawler = crawler
        self.fm = fm

    async def process_incremental_async(
        self, request: Request, result: List
    ) -> List[Union[Request, Item]]:
        """
        Processes the spider's parsing callbacks when IncrementalCrawlMiddleware is enabled.

        The function handles both requests and items returned by the spider.
        - If an item is found:
          - It saves the `request.url` and `item.url/item.canonicalURL` (if they differ) to the collection.
        - If the result is a Request:
          - It checks whether the request was processed previously.
          - If it was processed, the request is removed from the result.
          - If it was not, the request remains in the result.
        """
        item: Optional[Item] = None
        to_check = defaultdict(list)
        fingerprint_to_url_map: Set[Tuple[str, str]] = set()
        for i, element in enumerate(result):
            if isinstance(element, Request):
                # The requests are only checked to see if the links exist in the Collection
                fp = get_request_fingerprint(self.crawler, element)
                to_check[fp].append(i)
                self.crawler.stats.inc_value("incremental_crawling/requests_to_check")  # type: ignore[union-attr]
            else:
                if item:
                    raise NotImplementedError(
                        f"Unexpected number of returned items for {request.url}. "
                        f"None or one was expected."
                    )

                item = element
                unique_urls = self._get_unique_urls(request.url, item)
                for url, url_field in unique_urls.items():
                    fp = get_request_fingerprint(self.crawler, request.replace(url=url))
                    if url_field != "request_url":
                        to_check[fp].append(i)

                    # Storing the fingerprint-to-URL mapping for the item only.
                    # This will be used when storing the item in the Collection.
                    fingerprint_to_url_map.add((fp, url))

                    if url_field == "url":
                        self.crawler.stats.inc_value(  # type: ignore[union-attr]
                            "incremental_crawling/redirected_urls"
                        )
                        logger.debug(
                            f"Request URL for the item {request.url} was redirected to {url}."
                        )

        # Prepare list of duplications
        duplicated_fingerprints = await self.fm.get_existing_fingerprints_async(
            list(to_check.keys())
        )

        if duplicated_fingerprints:
            logging.debug(
                f"Skipping {len(duplicated_fingerprints)} Request fingerprints that were processed previously."
            )

        n_dups = 0
        for dupe_fp in duplicated_fingerprints:
            # Marking duplicates for removal as None
            for index in to_check[dupe_fp]:
                result[index] = None
                n_dups += 1

        filtered_result = [x for x in result if x is not None]

        self.crawler.stats.inc_value(  # type: ignore[union-attr]
            "incremental_crawling/filtered_items_and_requests", n_dups
        )
        # Check for any new fingerprints and their corresponding URLs for the item
        fingerprint_url_map_new = {
            (fp, url)
            for fp, url in fingerprint_to_url_map
            if fp not in duplicated_fingerprints
        }
        # Add any new fingerprints and their corresponding URLs to the batch for future saving
        if fingerprint_url_map_new:
            self.fm.add_to_batch(fingerprint_url_map_new)
        return filtered_result

    def _get_unique_urls(
        self, request_url: str, item: Optional[Item], discard_request_url: bool = False
    ) -> Dict[str, Optional[str]]:
        """Retrieves a dictionary of unique URLs associated with an item."""

        urls: Dict[str, Optional[str]] = {request_url: "request_url"}
        if not item:
            return urls

        url_fields = ["url", "canonicalUrl"]

        adapter = ItemAdapter(item)
        for url_field in url_fields:
            if (url := adapter[url_field]) and url not in urls:
                urls[url] = url_field

        if discard_request_url:
            urls.pop(request_url)

        return urls
