import html
import re
from collections import defaultdict
from logging import getLogger
from random import choice
from string import ascii_letters, digits
from urllib.parse import parse_qs, urlparse

import attrs
import extruct
import formasaurus
import jmespath
from form2request import form2request
from lxml import etree
from scrapy.http.response.html import HtmlResponse
from scrapy.linkextractors.lxmlhtml import LxmlLinkExtractor
from w3lib.url import add_or_replace_parameters
from web_poet import AnyResponse, PageParams, handle_urls
from web_poet.pages import validates_input
from zyte_common_items import SearchRequestTemplate, SearchRequestTemplatePage

logger = getLogger(__name__)

# Because Jinja2 syntax gets percent-encoded in a URL, we instead use a
# placeholder made of URL-safe characters, and replace it with Jinja2 code
# after URL encoding.
#
# We use a random placeholder instead of a readable one to minimize risk of
# accidental conflict, and we generate it at run time to minimize risk of
# purposeful conflict.
_url_safe_chars = ascii_letters + digits
_PLACEHOLDER = "".join(choice(_url_safe_chars) for _ in range(32))


def _any_http_response_to_scrapy_response(response: AnyResponse) -> HtmlResponse:
    kwargs = {}
    encoding = getattr(response, "_encoding", None) or "utf-8"
    kwargs["encoding"] = encoding
    kwargs["headers"] = getattr(response, "headers", {})
    return HtmlResponse(
        url=str(response.url), body=response.text, status=response.status, **kwargs
    )


@handle_urls("", priority=250)
@attrs.define
class DefaultSearchRequestTemplatePage(SearchRequestTemplatePage):
    response: AnyResponse  # type: ignore[assignment]
    page_params: PageParams

    def _item_from_form_heuristics(self):
        form_xpath = """
            //form[
                descendant-or-self::*[
                    contains(@action, "search")
                    or contains(@aria-label, "search")
                    or contains(@aria-labelledby, "search")
                    or contains(@class, "search")
                    or contains(@data-set, "search")
                    or contains(@formaction, "search")
                    or contains(@id, "search")
                    or contains(@role, "search")
                    or contains(@title, "search")
                ]
            ]
        """
        forms = self.response.xpath(form_xpath)
        if not forms:
            raise ValueError("No search forms found.")

        field_xpath = """
            descendant::textarea
                /@name
            | descendant::input[
                not(@type)
                or @type[
                    not(
                        re:test(
                            .,
                            "^(?:checkbox|image|radio|reset|submit)$",
                            "i"
                        )
                    )
                ]
            ]
                /@name
        """
        search_query_field = None
        for form in forms:
            search_query_field = form.xpath(field_xpath).get()
            if search_query_field:
                break
        if not search_query_field:
            raise ValueError(
                "No search query field found in any potential search form."
            )
        data = {search_query_field: _PLACEHOLDER}
        try:
            request_data = form2request(form, data)
        except NotImplementedError:
            raise ValueError("form2request does not support the target search form")
        return SearchRequestTemplate(
            url=request_data.url.replace(_PLACEHOLDER, "{{ query|quote_plus }}"),
            method=request_data.method,
            headers=request_data.headers,
            body=request_data.body.decode().replace(
                _PLACEHOLDER, "{{ query|quote_plus }}"
            ),
        )

    def _item_from_extruct(self):
        metadata = extruct.extract(
            self.response.text,
            base_url=str(self.response.url),
            syntaxes=["json-ld", "microdata"],
        )
        query_field = None
        for entry in metadata["microdata"]:
            if not (actions := entry.get("properties", {}).get("potentialAction", {})):
                continue
            if not isinstance(actions, list):
                actions = [actions]
            for action in actions:
                if action.get("type") != "https://schema.org/SearchAction":
                    continue
                url_template = jmespath.search(
                    "properties.target.urlTemplate || properties.target", action
                )
                if not url_template:
                    continue
                query_input = action.get("properties", {}).get("query-input", {})
                query_field = query_input.get("valueName", "search_term_string")
                break
            if query_field:
                break
        if not query_field:
            for entry in metadata["json-ld"]:
                action = jmespath.search(
                    '"@graph"[].potentialAction || isPartOf.potentialAction || potentialAction',
                    entry,
                )
                if not action:
                    continue
                if isinstance(action, list):
                    action = jmespath.search(
                        '([?"@type"==`SearchAction`] | [0]) || @', action
                    )
                if not action or action.get("@type") != "SearchAction":
                    continue
                url_template = jmespath.search("target.urlTemplate || target", action)
                if not url_template:
                    continue
                query_input = action.get(
                    "query-input", "required name=search_term_string"
                )
                query_field_match = re.search(r"\bname=(\S+)", query_input)
                if query_field_match:
                    query_field = query_field_match[1]
                else:
                    query_field = "search_term_string"
                break
                if query_field:
                    break
        if not query_field:
            raise ValueError(
                "Could not find HTML metadata to compose a search request template."
            )
        parts = url_template.split("?", maxsplit=1)
        parts[0] = parts[0].replace(f"{{{query_field}}}", "{{ query|urlencode }}")
        if len(parts) > 1:
            parts[1] = parts[1].replace(f"{{{query_field}}}", "{{ query|quote_plus }}")
        url = "?".join(parts)
        url = str(self.response.urljoin(url))
        url = html.unescape(url)
        return SearchRequestTemplate(
            url=url,
            method="GET",
            headers=[],
            body="",
        )

    def _item_from_link_heuristics(self):
        query_parameters = "|".join(
            (
                r"[a-z]?(?:(?:field|search)[_-]?)?key(?:word)?s?",
                r"[a-z]?(?:(?:field|search)[_-]?)?query",
                r"[a-z]?(?:(?:field|search)[_-]?)?params?",
                r"[a-z]?(?:(?:field|search)[_-]?)?terms?",
                r"[a-z]?(?:(?:field|search)[_-]?)?text",
                r"[a-z]?search",
                r"qs?",
                r"s",
            )
        )
        param_regexp = f"(?i)^(?:{query_parameters})$"
        url_regexp = f"(?i)[?&](?:{query_parameters})=(?!$)[^&]"
        netloc = urlparse(str(self.response.url)).netloc
        scrapy_response = _any_http_response_to_scrapy_response(self.response)
        try:
            search_links = LxmlLinkExtractor(
                allow=url_regexp, allow_domains=netloc
            ).extract_links(scrapy_response)
        except AttributeError as exception:
            raise ValueError(str(exception))
        if not search_links:
            raise ValueError(f"No valid search links found on {self.response.url}")
        for search_link in search_links:
            query_string = urlparse(search_link.url).query
            query = parse_qs(query_string)
            search_params = set()
            for k in query:
                if re.search(param_regexp, k):
                    search_params.add(k)
            if not search_params:
                continue
            url = add_or_replace_parameters(
                search_link.url, {k: _PLACEHOLDER for k in search_params}
            )
            url = url.replace(_PLACEHOLDER, "{{ query|quote_plus }}")
            return SearchRequestTemplate(
                url=url,
                method="GET",
                headers=[],
                body="",
            )
        raise ValueError(f"No valid search links found on {self.response.url}")

    def _item_from_formasaurus(self):
        try:
            form, data, submit_button = formasaurus.build_submission(
                self.response.selector,
                "search",
                {"search query": _PLACEHOLDER},
            )
        except AttributeError as exception:
            raise ValueError(str(exception))
        if not data:
            form_excerpt = etree.tostring(form).decode()[:64]
            if len(form_excerpt) >= 64:
                form_excerpt = form_excerpt[:-1] + "…"
            raise ValueError(
                f"Did not find an input field for the search query in "
                f"the most likely search form at {self.response.url} "
                f"(form_excerpt)."
            )
        try:
            request_data = form2request(form, data, click=submit_button)
        except NotImplementedError:
            raise ValueError("form2request does not support the target search form")
        return SearchRequestTemplate(
            url=request_data.url.replace(_PLACEHOLDER, "{{ query|quote_plus }}"),
            method=request_data.method,
            headers=request_data.headers,
            body=request_data.body.decode().replace(
                _PLACEHOLDER, "{{ query|quote_plus }}"
            ),
        )

    @validates_input
    async def to_item(self) -> SearchRequestTemplate:
        builders = {
            "extruct": self._item_from_extruct,
            "formasaurus": self._item_from_formasaurus,
            "link_heuristics": self._item_from_link_heuristics,
            "form_heuristics": self._item_from_form_heuristics,
        }
        builder_ids = self.page_params.get("search_request_builders", list(builders))
        builder_strategy = self.page_params.get(
            "search_request_builder_strategy", "popular"
        )
        if builder_strategy not in {"first", "popular"}:
            raise ValueError(
                f"Unsupported search_request_builder_strategy value: {builder_strategy!r}"
            )
        results = defaultdict(list)
        for builder_id in builder_ids:
            builder = builders[builder_id]
            try:
                result = builder()
            except ValueError:
                continue
            if result:
                if builder_strategy == "first":
                    return result
                results[(result.url, result.body)].append((builder_id, result))
        if results:
            assert builder_strategy == "popular"
            top_count = max(len(v) for v in results.values())
            top_results = {
                builder_id: result
                for result_list in results.values()
                for builder_id, result in result_list
                if len(result_list) == top_count
            }
            for builder_id in builder_ids:
                if builder_id not in top_results:
                    continue
                return top_results[builder_id]

        logger.error(
            f"Cannot build a search request template for "
            f"{self.response.url}. A quick workaround would be to use a "
            f"search URL as input URL instead of using the search "
            f"queries input field. You can also manually implement "
            f"search support for a given website "
            f"(https://zyte-common-items.readthedocs.io/en/latest/usage/re"
            f"quest-templates.html#writing-a-request-template-page-object)"
            f"."
        )
        return self.no_item_found()
