from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Union

from pydantic import BaseModel, Field, field_validator
from scrapy import Request
from scrapy.settings import SETTINGS_PRIORITIES, BaseSettings
from scrapy_poet import DummyResponse, DynamicDeps
from scrapy_spider_metadata import Args
from w3lib.url import add_or_replace_parameter
from zyte_common_items import (
    Article,
    ArticleList,
    ForumThread,
    JobPosting,
    Product,
    ProductList,
    Serp,
)

from .._geolocations import GEOLOCATION_OPTIONS_WITH_CODE, Geolocation
from ..documentation import document_enum
from ._google_domains import GoogleDomain
from ._google_gl import GOOGLE_GL_OPTIONS_WITH_CODE, GoogleGl
from ._google_hl import GOOGLE_HL_OPTIONS_WITH_CODE, GoogleHl
from .base import BaseSpider


class GoogleCrParam(BaseModel):
    cr: Optional[str] = Field(
        title="Content Countries (cr)",
        description=(
            "Restricts search results to documents originating in "
            "particular countries. See "
            "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.cr"
        ),
        default=None,
    )


class GoogleGlParam(BaseModel):
    gl: Optional[GoogleGl] = Field(
        title="User Country (gl)",
        description=(
            "Boosts results relevant to this country. See "
            "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.gl"
        ),
        default=None,
        json_schema_extra={
            "enumMeta": {
                code: {
                    "title": GOOGLE_GL_OPTIONS_WITH_CODE[code],
                }
                for code in GoogleGl
            }
        },
    )


class GoogleHlParam(BaseModel):
    hl: Optional[GoogleHl] = Field(
        title="User Language (hl)",
        description=(
            "User interface language, which can affect search results. See "
            "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.hl"
        ),
        default=None,
        json_schema_extra={
            "enumMeta": {
                code: {
                    "title": GOOGLE_HL_OPTIONS_WITH_CODE[code],
                }
                for code in GoogleHl
            }
        },
    )


class GoogleLrParam(BaseModel):
    lr: Optional[str] = Field(
        title="Content Languages (lr)",
        description=(
            "Restricts search results to documents written in the specified "
            "languages. See "
            "https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list#body.QUERY_PARAMETERS.lr"
        ),
        default=None,
    )


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


class SerpGeolocationParam(BaseModel):
    # We use “geolocation” as parameter name (instead of e.g. “ip_geolocation”)
    # to reuse the implementation in BaseSpider.
    geolocation: Optional[Geolocation] = Field(
        # The title, worded like this for contrast with gl, is the reason why
        # ..params.GeolocationParam is not used.
        title="IP Country",
        description="Country of the IP addresses to use.",
        default=None,
        json_schema_extra={
            "enumMeta": {
                code: {
                    "title": GEOLOCATION_OPTIONS_WITH_CODE[code],
                }
                for code in Geolocation
            }
        },
    )


class SerpMaxPagesParam(BaseModel):
    max_pages: int = Field(
        title="Max Pages",
        description="Maximum number of result pages to visit per search query.",
        ge=1,
        default=1,
    )


# MaxRequestsParam without the widget.
class SerpMaxRequestsParam(BaseModel):
    max_requests: Optional[int] = Field(
        description=(
            "The maximum number of Zyte API requests allowed for the crawl.\n"
            "\n"
            "Requests with error responses that cannot be retried or exceed "
            "their retry limit also count here, but they incur in no costs "
            "and do not increase the request count in Scrapy Cloud."
        ),
        default=100,
        ge=1,
    )


class SerpResultsPerPageParam(BaseModel):
    results_per_page: Optional[int] = Field(
        title="Results Per Page",
        description="Maximum number of results per page.",
        ge=1,
        default=None,
    )


@document_enum
class SerpItemType(str, Enum):
    off: str = "off"
    """
    Do not follow result links.
    """

    article: str = "article"
    """
    Article data.
    """

    articleList: str = "articleList"
    """
    Article list data.
    """

    forumThread: str = "forumThread"
    """
    Forum thread data.
    """

    jobPosting: str = "jobPosting"
    """
    Job posting data.
    """

    product: str = "product"
    """
    Product data.
    """

    productList: str = "productList"
    """
    Product list data.
    """


ITEM_TYPE_CLASSES = {
    SerpItemType.article: Article,
    SerpItemType.articleList: ArticleList,
    SerpItemType.forumThread: ForumThread,
    SerpItemType.jobPosting: JobPosting,
    SerpItemType.product: Product,
    SerpItemType.productList: ProductList,
}


class SerpItemTypeParam(BaseModel):
    item_type: SerpItemType = Field(
        title="Follow and Extract",
        description=(
            "If specified, follow organic search result links, and extract "
            "the selected data type from the target pages. Spider output "
            "items will be of the specified data type, not search engine "
            "results page items."
        ),
        default=SerpItemType.off,
    )


class GoogleDomainParam(BaseModel):
    domain: GoogleDomain = Field(
        title="Domain",
        description="Target Google domain.",
        default=GoogleDomain.google_com,
    )


class GoogleSearchSpiderParams(
    GoogleLrParam,
    GoogleHlParam,
    SerpGeolocationParam,
    GoogleCrParam,
    GoogleGlParam,
    SerpItemTypeParam,
    SerpResultsPerPageParam,
    SerpMaxPagesParam,
    SerpMaxRequestsParam,
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
    _default_results_per_page = 10

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
        for argument, parameter in (
            (self.args.cr, "cr"),
            (self.args.gl, "gl"),
            (self.args.hl, "hl"),
            (self.args.lr, "lr"),
            (self.args.results_per_page, "num"),
        ):
            if not argument:
                continue
            if isinstance(argument, Enum):
                argument = argument.value
            if not isinstance(argument, str):
                argument = str(argument)
            url = add_or_replace_parameter(url, parameter, argument)
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
            with self._log_request_exception:
                yield self.get_serp_request(search_url, page_number=1)

    def parse_serp(self, response, page_number) -> Iterable[Union[Request, Serp]]:
        serp = Serp.from_dict(response.raw_api_response["serp"])

        if page_number < self.args.max_pages:
            next_start = page_number * (
                self.args.results_per_page or self._default_results_per_page
            )
            if serp.organicResults and (
                serp.metadata.totalOrganicResults is None
                or serp.metadata.totalOrganicResults > next_start
            ):
                next_url = add_or_replace_parameter(serp.url, "start", str(next_start))
                with self._log_request_exception:
                    yield self.get_serp_request(next_url, page_number=page_number + 1)

        if self.args.item_type == SerpItemType.off:
            yield serp
            return

        for result in serp.organicResults:
            with self._log_request_exception:
                yield response.follow(
                    result.url,
                    callback=self.parse_result,
                    meta={
                        "crawling_logs": {"page_type": self.args.item_type.value},
                        "inject": [ITEM_TYPE_CLASSES[self.args.item_type]],
                    },
                )

    def parse_result(
        self, response: DummyResponse, dynamic: DynamicDeps
    ) -> Iterable[Any]:
        yield next(iter(dynamic.values()))
