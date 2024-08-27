.. _serp:

===============================
SERP spider template (``serp``)
===============================

Basic use
=========

.. code-block:: shell

    scrapy crawl serp -a url="https://www.google.com/search?q=foo"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.serp.SerpSpiderParams
    :inherited-members: BaseModel
    :exclude-members: model_computed_fields
