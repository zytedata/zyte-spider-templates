.. _spider-templates:

================
Spider templates
================

Built-in `spider templates`_ use `Zyte API automatic extraction`_ to provide
automatic crawling and parsing, i.e. you can run these spiders on any website
of the right type to automatically extract the desired structured data.

.. _spider templates: https://docs.zyte.com/scrapy-cloud/usage/spiders.html#spider-templates-and-virtual-spiders
.. _Zyte API automatic extraction: https://docs.zyte.com/zyte-api/usage/extract.html

For example, to extract all products from an e-commerce website, you can run
the :ref:`e-commerce spider <e-commerce>` spider as follows:

.. code-block:: shell

    scrapy crawl ecommerce -a url="https://books.toscrape.com"

Spider templates support additional parameters beyond ``url``. See the
documentation of each specific spider for details.

You can also :ref:`customize spider templates <customization>` to meet your
needs.

Spider template list
====================

:ref:`E-commerce <e-commerce>`
    Get products from an e-commerce website.

:ref:`Article <article>`
    Get articles from an article website.
