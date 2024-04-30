Changes
=======

0.7.2 (2024-MM-YY)
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
