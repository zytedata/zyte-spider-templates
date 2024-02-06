.. _e-commerce:

==========================================
E-commerce spider template (``ecommerce``)
==========================================

Basic use
=========

.. code-block:: shell

    scrapy crawl ecommerce -a url="https://books.toscrape.com"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.ecommerce.EcommerceSpiderParams
    :inherited-members: BaseModel
