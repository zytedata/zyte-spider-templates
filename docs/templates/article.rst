.. _article:

=====================================
Article spider template (``article``)
=====================================

Basic use
=========

.. code-block:: shell

    scrapy crawl article -a url="https://www.zyte.com/blog/"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.article.ArticleSpiderParams
    :inherited-members: BaseModel
    :exclude-members: model_computed_fields, single_input

Settings
========

The following :ref:`zyte-spider-templates settings <settings>` may be useful
for the article spider template:

:setting:`NAVIGATION_DEPTH_LIMIT`
    Limit the crawling depth of subcategories.

:setting:`OFFSITE_REQUESTS_PER_SEED_ENABLED`
    Skip follow-up requests if their URL points to a domain different from the
    domain of their initial URL.

:setting:`ONLY_FEEDS_ENABLED`
    Extract links only from Atom and RSS news feeds.
