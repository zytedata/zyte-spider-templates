=========
Reference
=========

Base classes
============

.. autoclass:: zyte_spider_templates.spiders.base.BaseSpider

.. autopydantic_model:: zyte_spider_templates.params.AllParams
    :inherited-members: BaseModel

.. autoenum:: zyte_spider_templates.params.CrawlStrategy

.. autoenum:: zyte_spider_templates.params.ExtractFrom

.. autoenum:: zyte_spider_templates.params.Geolocation

E-commerce
==========

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams
    :noindex:
    :inherited-members: BaseModel

Pages
=====

.. autoclass:: zyte_spider_templates.pages.HeuristicsProductNavigationPage
