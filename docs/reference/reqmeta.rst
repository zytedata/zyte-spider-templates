.. _meta:

=================
Request.meta keys
=================

Keys that can be defined in :attr:`Request.meta <scrapy.http.Request.meta>` for
zyte-spider-templates.

.. reqmeta:: seed

seed
====

Default: ``The seed URL (or value) from which the request originated.``

The key is used for :class:`~zyte_spider_templates.OffsiteRequestsPerSeedMiddleware` and
:class:`~zyte_spider_templates.MaxRequestsPerSeedDownloaderMiddleware`.

The `seed` meta key is used to track and identify the origin of a request. It
is initially set for each request that originates from the start request and
can be used to manage domain constraints for subsequent requests. This key can
also be set to an arbitrary value by the user to identify the seed source.

Here's an example:

.. code-block:: python

    meta = {
        "seed": "http://example.com",
    }

.. reqmeta:: is_seed_request

is_seed_request
===============

Default: ``False``

The key is used for :class:`~zyte_spider_templates.OffsiteRequestsPerSeedMiddleware`.

The `is_seed_request` meta key is a boolean flag that identifies whether the
request is a start request (i.e., originating from the initial seed URL). When
set to True, the middleware extracts seed domains from the response.

Example:
    ::

        meta = {
            'is_seed_request': True,
        }

.. reqmeta:: seed_domains

seed_domains
============

Default: ``Initial URL and redirected URLs``

The key is used for :class:`~zyte_spider_templates.OffsiteRequestsPerSeedMiddleware`.

The `seed_domains` meta key is a list of domains that the middleware uses to
check whether a request belongs to these domains or not. By default, this list
includes the initial URL's domain and domains of any redirected URLs `(if there
was a redirection)`. This list can also be set by the user in the spider to
specify additional domains for which the middleware should allow requests.

Here's an example:

.. code-block:: python

    meta = {"seed_domains": ["example.com", "another-example.com"]}

.. reqmeta:: is_hop

increase_navigation_depth
=========================

Default: ``True``

The key is used for :class:`~zyte_spider_templates.TrackNavigationDepthSpiderMiddleware`.

The `increase_navigation_depth` meta key is a boolean flag that determines whether the
navigation_depth for a request should be increased. By default, the middleware increases
navigation_depth for all requests. Specific spiders can override this behavior for certain
types of requests, such as pagination or RSS feeds, by explicitly setting the meta key.

Example:
    ::

        meta = {
            'increase_navigation_depth': False,
        }

.. reqmeta:: only_feeds

only_feeds
==========
Default: ``False``

The key is used for :class:`~zyte_spider_templates.OnlyFeedsMiddleware`.

The `only_feeds` meta key is a boolean flag that identifies whether the
spider should discover all links on the website or extract links from RSS/Atom feeds only.

Example:
    ::

        meta = {
            'page_params': {'only_feeds': True}
        }

