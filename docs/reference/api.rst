===
API
===

Spiders
=======

.. autoclass:: zyte_spider_templates.ArticleSpider

.. autoclass:: zyte_spider_templates.BaseSpider

.. autoclass:: zyte_spider_templates.EcommerceSpider

.. autoclass:: zyte_spider_templates.GoogleSearchSpider

.. autoclass:: zyte_spider_templates.JobPostingSpider


Pages
=====

.. autoclass:: zyte_spider_templates.pages.DefaultSearchRequestTemplatePage

.. autoclass:: zyte_spider_templates.pages.HeuristicsArticleNavigationPage

.. autoclass:: zyte_spider_templates.pages.HeuristicsProductNavigationPage


.. _parameter-mixins:

Parameter mixins
================

.. autopydantic_model:: zyte_spider_templates.params.CustomAttrsInputParam
    :exclude-members: model_computed_fields

.. autopydantic_model:: zyte_spider_templates.params.CustomAttrsMethodParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.params.CustomAttrsMethod

.. autopydantic_model:: zyte_spider_templates.params.ExtractFromParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.params.ExtractFrom

.. autopydantic_model:: zyte_spider_templates.params.GeolocationParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.params.Geolocation

.. autopydantic_model:: zyte_spider_templates.params.MaxRequestsParam
    :exclude-members: model_computed_fields

.. autopydantic_model:: zyte_spider_templates.params.UrlParam
    :exclude-members: model_computed_fields

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategyParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceExtractParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.ecommerce.EcommerceExtract

.. autopydantic_model:: zyte_spider_templates.spiders.serp.SerpItemTypeParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.serp.SerpItemType

.. autopydantic_model:: zyte_spider_templates.spiders.serp.SerpMaxPagesParam
    :exclude-members: model_computed_fields

.. autopydantic_model:: zyte_spider_templates.spiders.article.ArticleCrawlStrategyParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.article.ArticleCrawlStrategy

.. autopydantic_model:: zyte_spider_templates.spiders.job_posting.JobPostingCrawlStrategyParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.job_posting.JobPostingCrawlStrategy


.. _middlewares:

Middlewares
===========

.. autoclass:: zyte_spider_templates.CrawlingLogsMiddleware
.. autoclass:: zyte_spider_templates.TrackNavigationDepthSpiderMiddleware
.. autoclass:: zyte_spider_templates.MaxRequestsPerSeedDownloaderMiddleware
.. autoclass:: zyte_spider_templates.OffsiteRequestsPerSeedMiddleware
.. autoclass:: zyte_spider_templates.OnlyFeedsMiddleware
.. autoclass:: zyte_spider_templates.TrackSeedsSpiderMiddleware
.. autoclass:: zyte_spider_templates.IncrementalCrawlMiddleware
