from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from scrapy import Request
from scrapy.settings import SETTINGS_PRIORITIES, BaseSettings
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import Serp

from ..params import MaxRequestsParam
from ._google_domains import GoogleDomain
from .base import BaseSpider


class SearchQueriesParam(BaseModel):
    search_queries: Optional[List[str]] = Field(
        title="Search Queries",
        description="Input 1 search query per line (e.g. foo bar).",
        json_schema_extra={
            "widget": "textarea",
        },
    )

    @field_validator("search_queries", mode="before")
    @classmethod
    def validate_search_queries(cls, value: Union[List[str], str]) -> List[str]:
        """Validate a list of search queries.
        If a string is received as input, it is split into multiple strings
        on new lines.
        """
        if isinstance(value, str):
            value = value.split("\n")
        result = []
        for v in value:
            if v := v.strip():
                result.append(v)
        if not result:
            raise ValueError("The search_queries parameter value is missing or empty.")
        return result


class SerpMaxPagesParam(BaseModel):
    max_pages: int = Field(
        title="Max Pages",
        description="Maximum number of result pages to visit per search query.",
        ge=1,
        default=1,
    )


class GoogleDomainParam(BaseModel):
    domain: GoogleDomain = Field(
        title="Domain",
        description="Target Google domain.",
        default=GoogleDomain.google_com,
    )


class GoogleSearchSpiderParams(
    MaxRequestsParam,
    SerpMaxPagesParam,
    SearchQueriesParam,
    GoogleDomainParam,
    BaseModel,
):
    pass


class GoogleSearchSpider(Args[GoogleSearchSpiderParams], BaseSpider):
    """Yield results from Google searches.

    See :class:`~zyte_spider_templates.spiders.serp.GoogleSearchSpiderParams`
    for supported parameters.

    .. seealso:: :ref:`google-search`.
    """

    name = "google_search"
    _results_per_page = 10

    metadata: Dict[str, Any] = {
        **BaseSpider.metadata,
        "title": "Google Search Results",
        "description": "Template for spiders that extract Google search results.",
    }

    @classmethod
    def update_settings(cls, settings: BaseSettings) -> None:
        super().update_settings(settings)
        retry_policy_setting_priority = settings.getpriority("ZYTE_API_RETRY_POLICY")
        if (
            retry_policy_setting_priority is None
            or retry_policy_setting_priority < SETTINGS_PRIORITIES["spider"]
        ):
            settings.set(
                "ZYTE_API_RETRY_POLICY",
                "zyte_api.aggressive_retrying",
                priority="spider",
            )

    def get_serp_request(self, url: str, *, page_number: int):
        return Request(
            url=url,
            callback=self.parse_serp,
            cb_kwargs={
                "page_number": page_number,
            },
            meta={
                "crawling_logs": {"page_type": "serp"},
                "zyte_api": {
                    "serp": True,
                },
            },
        )

    def start_requests(self) -> Iterable[Request]:
        search_queries = self.args.search_queries
        if not search_queries:
            raise ValueError("No search queries specified.")

        url = f"https://www.{self.args.domain.value}/search"
        for search_query in search_queries:
            search_url = add_or_replace_parameter(url, "q", search_query)
            yield self.get_serp_request(search_url, page_number=1)

    def parse_serp(self, response, page_number) -> Iterable[Union[Request, Serp]]:
        serp = Serp.from_dict(response.raw_api_response["serp"])

        if page_number < self.args.max_pages:
            next_start = page_number * self._results_per_page
            if serp.organicResults and serp.metadata.totalOrganicResults > next_start:
                next_url = add_or_replace_parameter(serp.url, "start", str(next_start))
                yield self.get_serp_request(next_url, page_number=page_number + 1)

        yield serp
