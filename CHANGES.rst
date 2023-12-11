Changes
=======

0.4.0 (YYYY-MM-DD)
------------------

* Products outside of the domain can now be crawled using
  ``zyte_spider_templates.middlewares.AllowOffsiteMiddleware``.

* Updated documentation to also setup ``zyte_common_items.ZyteItemAdapter``.

* Improved ``max_requests`` spider parameter description.

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
