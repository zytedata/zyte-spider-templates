.. _settings:

========
Settings
========

.. setting:: NAVIGATION_DEPTH_LIMIT

NAVIGATION_DEPTH_LIMIT
======================

Default: ``0``

The maximum navigation depth to crawl. If ``0``, no limit is imposed.

We increase *navigation_depth* for requests navigating to a subcategory originating from
its parent category, including a request targeting a category starting at the website home page.
We don't increase *navigation_depth* for requests accessing item details (e.g., an article) or for
additional pages of a visited webpage. For example, if you set ``NAVIGATION_DEPTH_LIMIT`` to ``1``,
only item details and pagination links from your start URLs are followed.

.. note::
    Currently, only the :ref:`Article spider template <article>` implements proper
    navigation_depth support. Other spider templates treat all follow-up requests as
    increasing navigation_depth.

Setting a navigation_depth limit can prevent a spider from delving too deeply into
subcategories. This is especially useful if you only need data from the
top-level categories or specific subcategories.

When :ref:`customizing a spider template <custom-spiders>`, set the
:reqmeta:`increase_navigation_depth` request metadata key to override whether a request is
considered as increasing navigation depth (``True``) or not (``False``):

.. code-block:: python

    Request("https://example.com", meta={"increase_navigation_depth": False})

If you want to limit all link following, including pagination and item details,
consider using the :setting:`DEPTH_LIMIT <scrapy:DEPTH_LIMIT>` setting instead.

Implemented by :class:`~zyte_spider_templates.TrackNavigationDepthSpiderMiddleware`.

.. setting:: MAX_REQUESTS_PER_SEED

MAX_REQUESTS_PER_SEED
=====================

.. tip:: When using the :ref:`article spider template <article>`, you may use
    the
    :attr:`~zyte_spider_templates.spiders.article.ArticleSpiderParams.max_requests_per_seed`
    command-line parameter instead of this setting.

Default: ``0``

Limit the number of follow-up requests per initial URL to the specified amount.
Non-positive integers (i.e. 0 and below) imposes no limit and disables this middleware.

The limit is the total limit for all direct and indirect follow-up requests
of each initial URL.

Implemented by
:class:`~zyte_spider_templates.MaxRequestsPerSeedDownloaderMiddleware`.

.. setting:: OFFSITE_REQUESTS_PER_SEED_ENABLED

OFFSITE_REQUESTS_PER_SEED_ENABLED
=================================

Default: ``True``

Setting this value to ``True`` enables the
:class:`~zyte_spider_templates.OffsiteRequestsPerSeedMiddleware` while ``False``
completely disables it.

The middleware ensures that *most* requests would belong to the domain of the
seed URLs. However, it does allow offsite requests only if they were obtained
from a response that belongs to the domain of the seed URLs. Any other requests
obtained thereafter from a response in a domain outside of the seed URLs will
not be allowed.

This prevents the spider from completely crawling other domains while ensuring
that aggregator websites *(e.g. a news website with articles from other domains)*
are supported, as it can access pages from other domains.

Disabling the middleware would not prevent offsite requests from being filtered
and might generally lead in other domains from being crawled completely, unless
``allowed_domains`` is set in the spider.

.. note::

    If a seed URL gets redirected to a different domain, both the domain from
    the original request and the domain from the redirected response will be
    used as references.

    If the seed URL is `https://books.toscrape.com`, all subsequent requests to
    `books.toscrape.com` and its subdomains are allowed, but requests to
    `toscrape.com` are not. Conversely, if the seed URL is `https://toscrape.com`,
    requests to both `toscrape.com` and `books.toscrape.com` are allowed.

.. setting:: ONLY_FEEDS_ENABLED

ONLY_FEEDS_ENABLED
==================

.. note::

    Only works for the :ref:`article spider template <article>`.

Default: ``False``

Whether to extract links from Atom and RSS news feeds only (``True``) or
to also use extracted links from ``ArticleNavigation.subCategories`` (``False``).

Implemented by :class:`~zyte_spider_templates.OnlyFeedsMiddleware`.

.. setting:: INCREMENTAL_CRAWL_BATCH_SIZE

INCREMENTAL_CRAWL_BATCH_SIZE
============================

Default: ``50``

The maximum number of seen URLs to read from or write to the corresponding
:ref:`Zyte Scrapy Cloud collection <api-collections>` per request during an incremental
crawl (see :setting:`INCREMENTAL_CRAWL_ENABLED`).

This setting determines the batch size for interactions with the Collection.
If the response from a webpage contains more than 50 URLs, they will be split
into smaller batches for processing. Conversely, if fewer than 50 URLs are present,
all URLs will be handled in a single request to the Collection.

Adjusting this value can optimize the performance of a crawl by balancing the number
of requests sent to the Collection with processing efficiency.

.. note::

    Setting it too large (e.g. > 100) will cause issues due to the large query length.
    Setting it too small (less than 10) will remove the benefit of using a batch.

Implemented by :class:`~zyte_spider_templates.IncrementalCrawlMiddleware`.


.. setting:: INCREMENTAL_CRAWL_COLLECTION_NAME

INCREMENTAL_CRAWL_COLLECTION_NAME
=================================

.. note::

    :ref:`virtual spiders <virtual-spiders>` are spiders based on :ref:`spider templates <spider-templates>`.
    The explanation of using INCREMENTAL_CRAWL_COLLECTION_NAME related to both types of spiders.

.. tip:: When using the :ref:`article spider template <article>`, you may use
    the
    :attr:`~zyte_spider_templates.spiders.article.ArticleSpiderParams.incremental_collection_name`
    command-line parameter instead of this setting.


Default: `<The current spider's name>_incremental`.
The current spider's name here will be virtual spider's name, if it's a virtual spider;
otherwise, :data:`Spider.name <scrapy.Spider.name>`.

Name of the :ref:`Zyte Scrapy Cloud collection <api-collections>` used during
an incremental crawl (see :setting:`INCREMENTAL_CRAWL_ENABLED`).

By default, a collection named after the spider is used, meaning that matching URLs from
previous runs of the same spider are skipped, provided those previous runs had
the :setting:`INCREMENTAL_CRAWL_ENABLED` setting set to ``True`` or the spider
argument `incremental` set to `true`.

Using a different collection name makes sense, for example, in the following cases:
- Different spiders share a collection.
- The same spider uses different collections (e.g., for development runs vs. production runs).

Implemented by :class:`~zyte_spider_templates.IncrementalCrawlMiddleware`.


.. setting:: INCREMENTAL_CRAWL_ENABLED

INCREMENTAL_CRAWL_ENABLED
=========================

.. tip:: When using the :ref:`article spider template <article>`, you may use
    the
    :attr:`~zyte_spider_templates.spiders.article.ArticleSpiderParams.incremental`
    command-line parameter instead of this setting.

Default: ``False``

If set to ``True``, items seen in previous crawls with the same
:setting:`INCREMENTAL_CRAWL_COLLECTION_NAME` value are skipped.

Implemented by :class:`~zyte_spider_templates.IncrementalCrawlMiddleware`.
