from __future__ import annotations

from enum import Enum
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Union,
    cast,
)

import scrapy
from pydantic import BaseModel, ConfigDict, Field
from scrapy.crawler import Crawler
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import Args
from web_poet import BrowserResponse
from zyte_common_items import (
    CustomAttributes,
    JobPosting,
    JobPostingNavigation,
    ProbabilityRequest,
    SearchRequestTemplate,
)

from zyte_spider_templates.spiders.base import (
    ARG_SETTING_PRIORITY,
    INPUT_GROUP,
    BaseSpider,
)

from ..documentation import document_enum
from ..params import (
    CustomAttrsInputParam,
    CustomAttrsMethodParam,
    ExtractFrom,
    ExtractFromParam,
    GeolocationParam,
    MaxRequestsParam,
    SearchQueriesParam,
    UrlParam,
    UrlsFileParam,
    UrlsParam,
    parse_input_params,
)

if TYPE_CHECKING:
    # typing.Self requires Python 3.11
    from typing_extensions import Self


@document_enum
class JobPostingCrawlStrategy(str, Enum):
    navigation: str = "navigation"
    """Follow pagination and job posting detail pages."""

    direct_item: str = "direct_item"
    """Treat input URLs as direct links to job posting detail pages, and extract a
    job posting from each."""


class JobPostingCrawlStrategyParam(BaseModel):
    crawl_strategy: JobPostingCrawlStrategy = Field(
        title="Crawl strategy",
        description="Determines how input URLs and follow-up URLs are crawled.",
        default=JobPostingCrawlStrategy.navigation,
        json_schema_extra={
            "enumMeta": {
                JobPostingCrawlStrategy.navigation: {
                    "title": "Navigation",
                    "description": "Follow pagination and job posting detail pages.",
                },
                JobPostingCrawlStrategy.direct_item: {
                    "title": "Direct URLs to job postings",
                    "description": (
                        "Treat input URLs as direct links to job posting detail pages, and "
                        "extract a job posting from each."
                    ),
                },
            },
        },
    )


class JobPostingSearchQueriesParam(SearchQueriesParam):
    search_queries: List[str] = Field(
        title="Search Queries",
        description=(
            "A list of search queries, one per line, to submit using the "
            "search form found on each input URL. Only works for input URLs "
            "that support search. May not work on every website."
        ),
        default_factory=list,
        json_schema_extra={
            "default": [],
            "widget": "textarea",
        },
    )


class JobPostingSpiderParams(
    CustomAttrsMethodParam,
    CustomAttrsInputParam,
    ExtractFromParam,
    MaxRequestsParam,
    GeolocationParam,
    JobPostingCrawlStrategyParam,
    JobPostingSearchQueriesParam,
    UrlsFileParam,
    UrlsParam,
    UrlParam,
    BaseModel,
):
    model_config = ConfigDict(
        json_schema_extra={
            "groups": [
                INPUT_GROUP,
            ],
        },
    )


class JobPostingSpider(Args[JobPostingSpiderParams], BaseSpider):
    """Yield job postings from a job website.

    See :class:`~zyte_spider_templates.spiders.job_posting.JobPostingSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`job-posting`.
    """

    name = "job_posting"

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "Job posting",
        "description": "[Experimental] Template for spiders that extract job posting data from websites.",
    }

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs) -> Self:
        spider = super().from_crawler(crawler, *args, **kwargs)
        parse_input_params(spider)
        spider._init_extract_from()
        return spider

    def _init_extract_from(self):
        if self.args.extract_from is not None:
            self.settings.set(
                "ZYTE_API_PROVIDER_PARAMS",
                {
                    "jobPostingOptions": {"extractFrom": self.args.extract_from},
                    "jobPostingNavigationOptions": {
                        "extractFrom": self.args.extract_from
                    },
                    **self.settings.get("ZYTE_API_PROVIDER_PARAMS", {}),
                },
                priority=ARG_SETTING_PRIORITY,
            )

    def get_start_request(self, url):
        callback = (
            self.parse_job_posting
            if self.args.crawl_strategy == JobPostingCrawlStrategy.direct_item
            else self.parse_navigation
        )
        meta: Dict[str, Any] = {
            "crawling_logs": {
                "page_type": "jobPosting"
                if self.args.crawl_strategy == JobPostingCrawlStrategy.direct_item
                else "jobPostingNavigation"
            },
        }
        if (
            self.args.crawl_strategy == JobPostingCrawlStrategy.direct_item
            and self._custom_attrs_dep
        ):
            meta["inject"] = [
                self._custom_attrs_dep,
            ]
        return scrapy.Request(
            url=url,
            callback=callback,
            meta=meta,
        )

    def start_requests(self) -> Iterable[scrapy.Request]:
        if self.args.search_queries:
            for url in self.start_urls:
                meta: Dict[str, Any] = {
                    "crawling_logs": {"page_type": "searchRequestTemplate"},
                }
                if self.args.extract_from == ExtractFrom.browserHtml:
                    meta["inject"] = [BrowserResponse]
                with self._log_request_exception:
                    yield scrapy.Request(
                        url=url,
                        callback=self.parse_search_request_template,
                        meta=meta,
                    )
        else:
            for url in self.start_urls:
                with self._log_request_exception:
                    yield self.get_start_request(url)

    def parse_search_request_template(
        self,
        response: DummyResponse,
        search_request_template: SearchRequestTemplate,
        dynamic: DynamicDeps,
    ) -> Iterable[scrapy.Request]:
        probability = search_request_template.get_probability()
        if probability is not None and probability <= 0:
            return
        for query in self.args.search_queries:
            meta: Dict[str, Any] = {
                "crawling_logs": {"page_type": "jobPostingNavigation"},
            }
            with self._log_request_exception:
                yield search_request_template.request(query=query).to_scrapy(
                    callback=self.parse_navigation,
                    meta=meta,
                )

    def parse_navigation(
        self, response: DummyResponse, navigation: JobPostingNavigation
    ) -> Iterable[scrapy.Request]:
        job_postings = navigation.items or []
        for request in job_postings:
            with self._log_request_exception:
                yield self.get_parse_job_posting_request(request)

        if navigation.nextPage:
            if not job_postings:
                self.logger.info(
                    f"Ignoring nextPage link {navigation.nextPage} since there "
                    f"are no job posting links found in {navigation.url}"
                )
            else:
                with self._log_request_exception:
                    yield self.get_nextpage_request(
                        cast(ProbabilityRequest, navigation.nextPage)
                    )

    def parse_job_posting(
        self, response: DummyResponse, job_posting: JobPosting, dynamic: DynamicDeps
    ) -> Iterable[
        Union[JobPosting, Dict[str, Union[JobPosting, Optional[CustomAttributes]]]]
    ]:
        probability = job_posting.get_probability()

        # TODO: convert to a configurable parameter later on after the launch
        if probability is None or probability >= 0.1:
            if self.args.custom_attrs_input:
                yield {
                    "jobPosting": job_posting,
                    "customAttributes": dynamic.get(CustomAttributes),
                }
            else:
                yield job_posting
        else:
            assert self.crawler.stats
            self.crawler.stats.inc_value("drop_item/job_posting/low_probability")
            self.logger.info(
                f"Ignoring item from {response.url} since its probability is "
                f"less than threshold of 0.1:\n{job_posting}"
            )

    def get_parse_navigation_request(
        self,
        request: ProbabilityRequest,
        callback: Optional[Callable] = None,
        page_params: Optional[Dict[str, Any]] = None,
        page_type: str = "jobPostingNavigation",
    ) -> scrapy.Request:
        callback = callback or self.parse_navigation

        return request.to_scrapy(
            callback=callback,
            meta={
                "page_params": page_params or {},
                "crawling_logs": {
                    "name": request.name or "",
                    "probability": request.get_probability(),
                    "page_type": page_type,
                },
            },
        )

    def get_nextpage_request(
        self,
        request: ProbabilityRequest,
        callback: Optional[Callable] = None,
        page_params: Optional[Dict[str, Any]] = None,
    ):
        return self.get_parse_navigation_request(
            request, callback, page_params, "nextPage"
        )

    def get_parse_job_posting_request(
        self, request: ProbabilityRequest, callback: Optional[Callable] = None
    ) -> scrapy.Request:
        callback = callback or self.parse_job_posting

        probability = request.get_probability()
        meta: Dict[str, Any] = {
            "crawling_logs": {
                "name": request.name,
                "probability": probability,
                "page_type": "jobPosting",
            },
        }
        if self._custom_attrs_dep:
            meta["inject"] = [
                self._custom_attrs_dep,
            ]

        scrapy_request = request.to_scrapy(
            callback=callback,
            meta=meta,
        )
        scrapy_request.meta["allow_offsite"] = True
        return scrapy_request
