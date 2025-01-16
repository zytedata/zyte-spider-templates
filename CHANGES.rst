Changes
=======

0.11.2 (2024-12-30)
-------------------

* Do not log warning about disabled components.

0.11.1 (2024-12-26)
-------------------

* The :ref:`e-commerce <e-commerce>` and :ref:`job posting <job-posting>`
  spider templates no longer ignore item requests for a different domain.

0.11.0 (2024-12-16)
-------------------

* New :ref:`Articles spider template <article>`, built on top of
  Zyte API’s :http:`request:article` and :http:`request:articleNavigation`.

* New :ref:`Job Posting spider template <job-posting>`, built on top of
  Zyte API’s :http:`request:jobPosting` and :http:`request:jobPostingNavigation`.

* :ref:`Search queries <search-queries>` support is added to the
  :ref:`e-commerce spider template <e-commerce>`.
  This allows to provide a list of search queries to the
  spider; the spider finds a search form on the target webpage, and submits all the queries.

* ProductList extraction support is added to the
  :ref:`e-commerce spider template <e-commerce>`. This allows spiders to
  extract basic product information without going into product detail pages.

* New features are added to the :ref:`Google Search spider template <google-search>`:

    * An option to follow the result links and extract data
      from the target pages (via the ``extract`` argument)
    * Content Languages (lr) parameter
    * Content Countries (cr) parameter
    * User Country (gl) parameter
    * User Language (hl) parameter
    * results_per_page parameter

* Added a Scrapy add-on. This allows to greatly simplify the initial
  zyte-spider-templates configuration.

* Bug fix: incorrectly extracted URLs no longer make spiders drop
  other requests.

* Cleaned up the CI; improved the testing suite; cleaned up the documentation.

0.10.0 (2024-11-22)
-------------------

* Dropped Python 3.8 support, added Python 3.13 support.

* Increased the minimum required versions of some dependencies:

  * ``pydantic``: ``2`` → ``2.1``

  * ``scrapy-poet``: ``0.21.0`` → ``0.24.0``

  * ``scrapy-spider-metadata``: ``0.1.2`` → ``0.2.0``

  * ``scrapy-zyte-api[provider]``: ``0.16.0`` → ``0.23.0``

  * ``zyte-common-items``: ``0.22.0`` → ``0.23.0``

* Added :ref:`custom attributes <custom-attributes>` support to the
  :ref:`e-commerce spider template <e-commerce>` through its new
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.custom_attrs_input`
  and
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.custom_attrs_method`
  parameters.

* The
  :class:`~zyte_spider_templates.spiders.serp.GoogleSearchSpiderParams.max_pages`
  parameter of the :ref:`Google Search spider template <google-search>` can no
  longer be 0 or lower.

* The :ref:`Google Search spider template <google-search>` now follows
  pagination for the results of each query page by page, instead of sending a
  request for every page in parallel. It stops once it reaches a page without
  organic results.

* Improved the description of
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy`
  values.

* Fixed type hint issues related to Scrapy.


0.9.0 (2024-09-17)
------------------

* Now requires ``zyte-common-items >= 0.22.0``.

* New :ref:`Google Search spider template <google-search>`, built on top of
  Zyte API’s :http:`request:serp`.

* The heuristics of the :ref:`e-commerce spider template <e-commerce>` to
  ignore certain URLs when following category links now also handles
  subdomains. For example, before https://example.com/blog was ignored, now
  https://blog.example.com is also ignored.

* In the :ref:`spider parameters JSON schema <params-schema>`, the
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.crawl_strategy`
  parameter of the :ref:`e-commerce spider template <e-commerce>` switches
  position, from being the last parameter to being between
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.urls_file`
  and
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.geolocation`.

* Removed the ``valid_page_types`` attribute of
  :class:`zyte_spider_templates.middlewares.CrawlingLogsMiddleware`.


0.8.0 (2024-08-21)
------------------

* Added new input parameters:

  * ``urls`` accepts a newline-delimited list of URLs.

  * ``urls_file`` accepts a URL that points to a plain-text file with a
    newline-delimited list of URLs.

  Only one of ``url``, ``urls`` and ``urls_file`` should be used at a time.

* Added new crawling strategies:

  * ``automatic`` - uses heuristics to see if an input URL is a homepage, for
    which it uses a modified ``full`` strategy where other links are discovered
    only in the homepage. Otherwise, it assumes it's a navigation page and uses
    the existing ``navigation`` strategy.

  * ``direct_item`` - input URLs are directly extracted as products.

* Added new parameters classes: ``LocationParam`` and ``PostalAddress``. Note
  that these are available for use when customizing the templates and are not
  currently being utilized by any template.

* Backward incompatible changes:

  * ``automatic`` becomes the new default crawling strategy instead of ``full``.

* CI test improvements.


0.7.2 (2024-05-07)
------------------

* Implemented :ref:`mixin classes for spider parameters <parameter-mixins>`, to
  improve reuse.

* Improved docs, providing an example about overriding existing parameters when
  :ref:`customizing parameters <custom-params>`, and featuring
  :class:`~web_poet.AnyResponse` in the :ref:`example about overriding parsing
  <override-parsing>`.


0.7.1 (2024-02-22)
------------------

* The
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams.crawl_strategy`
  parameter of
  :class:`~zyte_spider_templates.spiders.ecommerce.EcommerceSpider`
  now defaults to
  :attr:`~zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy.full`
  instead of
  :attr:`~zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy.navigation`.
  We also reworded some descriptions of :enum:`~.EcommerceCrawlStrategy` values
  for clarification.

0.7.0 (2024-02-09)
------------------

* Updated requirement versions:

  * :doc:`scrapy-poet <scrapy-poet:index>` >= 0.21.0
  * :doc:`scrapy-zyte-api <scrapy-zyte-api:index>` >= 0.16.0

* With the updated dependencies above, this fixes the issue of having 2 separate
  Zyte API Requests (*productNavigation* and *httpResponseBody*) for the same URL. Note
  that this issue only occurs when requesting product navigation pages.

* Moved :class:`zyte_spider_templates.spiders.ecommerce.ExtractFrom` into
  :class:`zyte_spider_templates.spiders.base.ExtractFrom`.


0.6.1 (2024-02-02)
------------------

* Improved the :attr:`zyte_spider_templates.spiders.base.BaseSpiderParams.url`
  description.

0.6.0 (2024-01-31)
------------------

* Fixed the ``extract_from`` spider parameter that wasn't working.

* The *"www."* prefix is now removed when setting the spider's
  :attr:`~scrapy.Spider.allowed_domains`.

* The :attr:`zyte_common_items.ProductNavigation.nextPage` link won't be crawled
  if :attr:`zyte_common_items.ProductNavigation.items` is empty.

* :class:`zyte_common_items.Product` items that are dropped due to low probability
  *(below 0.1)* are now logged in stats: ``drop_item/product/low_probability``.

* :class:`zyte_spider_templates.pages.HeuristicsProductNavigationPage` now
  inherits from :class:`zyte_common_items.AutoProductNavigationPage` instead of
  :class:`zyte_common_items.BaseProductNavigationPage`.

* Moved e-commerce code from :class:`zyte_spider_templates.spiders.base.BaseSpider`
  to :class:`zyte_spider_templates.spiders.ecommerce.EcommerceSpider`.

* Documentation improvements.

0.5.0 (2023-12-18)
------------------

* The ``zyte_spider_templates.page_objects`` module is now deprecated in favor
  of ``zyte_spider_templates.pages``, in line with ``web_poet.pages``.

0.4.0 (2023-12-14)
------------------

* Products outside of the target domain can now be crawled using
  :class:`zyte_spider_templates.middlewares.AllowOffsiteMiddleware`.

* Updated the documentation to also set up ``zyte_common_items.ZyteItemAdapter``.

* The ``max_requests`` spider parameter has now a default value of 100. Previously,
  it was ``None`` which was unlimited.

* Improved the description of the ``max_requests`` spider parameter.

* Official support for Python 3.12.

* Misc documentation improvements.

0.3.0 (2023-11-03)
------------------

* Added documentation.

* Added a middleware that logs information about the crawl in JSON format,
  :class:`zyte_spider_templates.middlewares.CrawlingLogsMiddleware`. This
  replaces the old crawling information that was difficult to parse using
  regular expressions.

0.2.0 (2023-10-30)
------------------

* Now requires ``zyte-common-items >= 0.12.0``.

* Added a new crawl strategy, "Pagination Only".

* Improved the request priority calculation based on the metadata probability
  value.

* CI improvements.


0.1.0 (2023-10-24)
------------------

Initial release.
