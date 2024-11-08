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
    from zyte_common_items import BaseSearchRequestTemplatePage


    @handle_urls("example.com")
    class ExampleComSearchRequestTemplatePage(BaseSearchRequestTemplatePage):
        @field
        def url(self):
            return "https://example.com/search?q={{ keyword|quote_plus }}"
