.. _search-keywords:

===============
Search keywords
===============

The :ref:`e-commerce spider template <e-commerce>` supports a spider argument,
:data:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.search_keywords`,
that allows you to define a different set of search keywords per line, and
turns the input URLs into search requests for those keywords.

For example, given the following input URLs:

.. code-block:: none

    https://a.example
    https://b.example

And the following list of search keywords:

.. code-block:: none

    foo bar
    baz

By default, the spider would send 2 initial requests to those 2 input URLs,
to try and find out how to build a search request for them, and if it succeeds,
it will then send 4 search requests, 1 per combination of input URL and search
keywords line. For example:

.. code-block:: none

    https://a.example/search?q=foo+bar
    https://a.example/search?q=baz
    https://b.example/s/foo%20bar
    https://b.example/s/baz

The default implementation uses a combination of HTML metadata, AI-based HTML
form inspection and heuristics to find the most likely way to build a search
request for a given website.

If this default implementation does not work as expected on a given website,
you can :ref:`write a page object to fix that <fix-search>`.
