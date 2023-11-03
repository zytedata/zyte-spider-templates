Changes
=======

0.3.0 (YYYY-MM-DD)
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
