=========
Reference
=========

Spiders
=======

.. autoclass:: zyte_spider_templates.BaseSpider

.. autoclass:: zyte_spider_templates.EcommerceSpider

.. autoclass:: zyte_spider_templates.GoogleSearchSpider


Pages
=====

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

.. autopydantic_model:: zyte_spider_templates.spiders.serp.SerpItemTypeParam
    :exclude-members: model_computed_fields

.. autoenum:: zyte_spider_templates.spiders.serp.SerpItemType

.. autopydantic_model:: zyte_spider_templates.spiders.serp.SerpMaxPagesParam
    :exclude-members: model_computed_fields
