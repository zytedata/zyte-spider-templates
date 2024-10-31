.. _custom-page-objects:

========================
Customizing page objects
========================

All parsing is implemented using :ref:`web-poet page objects <page-objects>`
that use `Zyte API automatic extraction`_ to extract :ref:`standard items
<item-api>`: for navigation, for item details, and even for :ref:`search
request generation <search-queries>`.

.. _Zyte API automatic extraction: https://docs.zyte.com/zyte-api/usage/extract.html

You can implement your own page object classes to override how extraction works
for any given combination of URL and item type.

.. tip:: Make sure the import path of your page objects module is in the
    :ref:`SCRAPY_POET_DISCOVER <scrapy-poet:settings>` setting, otherwise your
    page objects might be ignored.

.. _configured scrapy-poet: https://scrapy-poet.readthedocs.io/en/stable/intro/install.html#configuring-the-project

.. _override-parsing:

Overriding parsing
==================

To change or fix how a given field is extracted, overriding the value from
`Zyte API automatic extraction`_, create a page object class, configured to run
on some given URLs (:func:`web_poet.handle_urls`), that defines the logic to
extract that field. For example:

.. code-block:: python
    :caption: pages/books_toscrape_com.py

    import attrs
    from number_parser import parse_number
    from web_poet import AnyResponse, field, handle_urls
    from zyte_common_items import AggregateRating, AutoProductPage


    @handle_urls("books.toscrape.com")
    @attrs.define
    class BooksToScrapeComProductPage(AutoProductPage):
        response: AnyResponse

        @field
        async def aggregateRating(self):
            element_class = self.response.css(".star-rating::attr(class)").get()
            if not element_class:
                return None
            rating_str = element_class.split(" ")[-1]
            rating = parse_number(rating_str)
            if not rating:
                return None
            return AggregateRating(ratingValue=rating, bestRating=5)

``AutoProductPage`` and other page objects from `zyte-common-items`_
prefixed with ``Auto`` define fields for all standard items that return
the value from `Zyte API automatic extraction`_, so that you only need
to define your new field.

.. _zyte-common-items: https://zyte-common-items.readthedocs.io/en/latest/

The page object above is decorated with ``@attrs.define`` so that it can
declare a dependency on :class:`~web_poet.page_inputs.response.AnyResponse` and
use that to implement custom parsing logic. You could alternatively use
:class:`~web_poet.page_inputs.browser.BrowserHtml` if needed.


.. _add-field:

Parsing a new field
===================

To extract a new field for one or more websites:

#.  Declare a new item type that extends a :ref:`standard item <item-api>` with
    your new field. For example:

    .. code-block:: python
        :caption: items.py

        from typing import Optional

        import attrs
        from zyte_common_items import Product


        @attrs.define
        class CustomProduct(Product):
            stock: Optional[int]

#.  Create a page object class, configured to run for your new item type
    (:class:`web_poet.pages.Returns`) on some given URLs
    (:func:`web_poet.handle_urls`), that defines the logic to extract your new
    field. For example:

    .. code-block:: python
        :caption: pages/books_toscrape_com.py

        import re

        from web_poet import Returns, field, handle_urls
        from zyte_common_items import AutoProductPage

        from ..items import CustomProduct


        @handle_urls("books.toscrape.com")
        class BookPage(AutoProductPage, Returns[CustomProduct]):
            @field
            async def stock(self):
                for entry in await self.additionalProperties:
                    if entry.name == "availability":
                        match = re.search(r"\d([.,\s]*\d+)*(?=\s+available\b)", entry.value)
                        if not match:
                            return None
                        stock_str = re.sub(r"[.,\s]", "", match[0])
                        return int(stock_str)
                return None

#.  Create a spider template subclass that requests your new item type instead
    of the standard one. For example:

    .. code-block:: python
        :caption: spiders/books_toscrape_com.py

        from scrapy_poet import DummyResponse
        from zyte_spider_templates import EcommerceSpider

        from ..items import CustomProduct


        class BooksToScrapeComSpider(EcommerceSpider):
            name = "books_toscrape_com"
            metadata = {
                **EcommerceSpider.metadata,
                "title": "Books to Scrape",
                "description": "Spider template for books.toscrape.com",
            }

            def parse_product(self, response: DummyResponse, product: CustomProduct):
                yield from super().parse_product(response, product)

.. _fix-search:

Fixing search support
=====================

If the default implementation to build a request out of :ref:`search queries
<search-queries>` does not work on a given website, you can implement your
own search request page object to fix that. See
:ref:`custom-request-template-page`.

For example:

.. code-block:: python

    from web_poet import handle_urls
    from zyte_common_items import SearchRequestTemplatePage


    @handle_urls("example.com")
    class ExampleComSearchRequestTemplatePage(SearchRequestTemplatePage):
        @field
        def url(self):
            return "https://example.com/search?q={{ keyword|quote_plus }}"


Reusing the default implementation
----------------------------------

The default implementation of search request building combines the following
*builders*, pieces of code that each can determine how to build a search
request from a given web page using a different approach:

-   ``extruct``: Uses the extruct_ library to build a request based on
    SearchAction_ metadata.

    .. _extruct: https://github.com/scrapinghub/extruct
    .. _SearchAction: https://schema.org/SearchAction

-   ``formasaurus``: Uses the AI-powered :doc:`Formasaurus <formasaurus:index>`
    library to find a search form, and builds a request out of it with the
    :doc:`form2request <form2request:index>` library.

-   ``link_heuristics``: Uses heuristics to find a link that looks like a
    search link, and builds a GET request with a URL based on that search link.

-   ``form_heuristics``: Uses heuristics to find a form that look like a search
    form, and builds a request out of it with the :doc:`form2request
    <form2request:index>` library.

By default, the first builder from the list above is used, but if multiple
builders yield the same search request, that search request is preferred.

This is implemented in the
:class:`zyte_spider_templates.pages.search_request_template.DefaultSearchRequestTemplatePage`
page object class, which supports :ref:`page params <page-params>` to modify
which builders are used, in which order, and with which strategy:

-   ``search_request_builders`` determines which builders to use and their
    order of precedence.

    Default: ``["extruct", "formasaurus", "link_heuristics", "form_heuristics"]``

-   ``search_request_builder_strategy`` determines the strategy to use among
    these:

    -   ``"first"``: Builders are executed in order of precedence, and the
        first solution is used. Builders that do not yield a solution at all
        are ignored.

    -   ``"popular"`` (default): Runs every builder and picks the most common
        solution. If there is not a single most common solution, then the order
        of precedence of builders is taken into account.

If the default implementation does not work for a given website, but a specific
builder does work, you could implement a search request template page object
class that subclasses this one and changes the strategy and builders.

For example, if a website defines valid SearchAction_ metadata, you can force
that metadata to be used for that website with the following page object class:

.. code-block:: python

    import attrs
    from web_poet import handle_urls
    from zyte_common_items import SearchRequestTemplatePage
    from zyte_spider_templates.pages.search_request_template import (
        DefaultSearchRequestTemplatePage,
    )


    @handle_urls("example.com")
    @attrs.define
    class ExampleComSearchRequestTemplatePage(DefaultSearchRequestTemplatePage):
        def __attrs_post_init__(self):
            self.page_params.setdefault("search_request_builder_strategy", "first")
            self.page_params.setdefault("search_request_builders", ["extruct"])
