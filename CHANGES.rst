Changes
=======

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
