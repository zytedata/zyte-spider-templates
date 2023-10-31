.. _e-commerce:

===========================================
E-commerce spider template (``e-commerce``)
===========================================

Basic use
=========

.. code-block:: shell

    scrapy crawl e-commerce -a url="https://books.toscrape.com"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams
    :inherited-members: BaseModel

.. autoenum:: zyte_spider_templates.spiders.ecommerce.EcommerceCrawlStrategy

.. autoenum:: zyte_spider_templates.spiders.ecommerce.ExtractFrom

.. autoenum:: zyte_spider_templates.spiders.base.Geolocation
