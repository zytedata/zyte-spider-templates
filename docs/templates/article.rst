.. _article:

==========================================
Article spider template (``article``)
==========================================

Basic use
=========

.. code-block:: shell

    scrapy crawl article -a url="https://quotes.toscrape.com/"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.article.ArticleSpiderParams
    :inherited-members: BaseModel

.. autoenum:: zyte_spider_templates.spiders.article.ArticleCrawlStrategy

.. autoenum:: zyte_spider_templates.spiders.base.ExtractFrom

.. autoenum:: zyte_spider_templates.spiders.base.Geolocation
