=========
Reference
=========

Base classes
============

.. autopydantic_model:: zyte_spider_templates.spiders.base.BaseSpiderParams
    :inherited-members: BaseModel

.. autoclass:: zyte_spider_templates.spiders.base.BaseSpider

.. autoenum:: zyte_spider_templates.spiders.base.ExtractFrom
    :noindex:

.. autoenum:: zyte_spider_templates.spiders.base.Geolocation
    :noindex:

E-commerce
==========

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams
    :noindex:
    :inherited-members: BaseModel

.. autoenum:: zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy
    :noindex:

.. autoclass:: zyte_spider_templates.spiders.ecommerce.EcommerceSpider

Pages
=====

.. autoclass:: zyte_spider_templates.pages.HeuristicsProductNavigationPage
