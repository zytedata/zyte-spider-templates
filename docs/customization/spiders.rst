.. _custom-spiders:

============================
Customizing spider templates
============================

Subclass a :ref:`built-in spider template <spider-templates>` to customize its
:ref:`metadata <custom-metadata>`, :ref:`parameters <custom-params>`, and
:ref:`crawling logic <custom-crawl>`.

.. _custom-metadata:

Customizing metadata
====================

Spider template metadata is defined using `scrapy-spider-metadata`_, and can be
`redefined or customized in a subclass`_.

For example, to keep the upstream ``title`` but change the ``description``:

.. _redefined or customized in a subclass: https://scrapy-spider-metadata.readthedocs.io/en/latest/metadata.html#defining-spider-metadata

.. code-block:: python

    from zyte_spider_templates import EcommerceSpider


    class MySpider(EcommerceSpider):
        name = "my_spider"
        metadata = {
            **EcommerceSpider.metadata,
            "description": "Custom e-commerce spider template.",
        }


.. _custom-params:

Customizing parameters
======================

Spider template parameters are also defined using `scrapy-spider-metadata`_,
and can be `redefined or customized in a subclass as well`_.

For example, to add a ``min_price`` parameter and filter out products with a
lower price:

.. _redefined or customized in a subclass as well: https://scrapy-spider-metadata.readthedocs.io/en/latest/params.html

.. code-block:: python

    from decimal import Decimal
    from typing import Iterable

    from scrapy_poet import DummyResponse
    from scrapy_spider_metadata import Args
    from zyte_common_items import Product
    from zyte_spider_templates import EcommerceSpider
    from zyte_spider_templates.spiders.ecommerce import EcommerceSpiderParams


    class MyParams(EcommerceSpiderParams):
        min_price: str = "0.00"


    class MySpider(EcommerceSpider, Args[MyParams]):
        name = "my_spider"

        def parse_product(
            self, response: DummyResponse, product: Product
        ) -> Iterable[Product]:
            for product in super().parse_product(response, product):
                if Decimal(product.price) >= Decimal(self.args.min_price):
                    yield product


.. _custom-crawl:

Customizing the crawling logic
==============================

The crawling logic of spider templates can be customized as any other
:ref:`Scrapy spider <topics-spiders>`.

For example, you can make a spider that expects a product details URL and does
not follow navigation at all:

.. code-block:: python

    from typing import Iterable

    from scrapy import Request
    from zyte_spider_templates import EcommerceSpider


    class MySpider(EcommerceSpider):
        name = "my_spider"

        def start_requests(self) -> Iterable[Request]:
            for request in super().start_requests():
                yield request.replace(callback=self.parse_product)

All parsing logic is implemented separately in :ref:`page objects
<custom-page-objects>`, making it easier to read the code of :ref:`built-in
spider templates <spider-templates>` to modify them as desired.

.. _scrapy-spider-metadata: https://scrapy-spider-metadata.readthedocs.io/en/latest
