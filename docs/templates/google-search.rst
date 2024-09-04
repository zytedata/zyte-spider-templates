.. _google-search:

=================================================
Google search spider template (``google_search``)
=================================================

Basic use
=========

.. code-block:: shell

    scrapy crawl google_search -a search_keywords="foo bar"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.serp.GoogleSearchSpiderParams
    :inherited-members: BaseModel
    :exclude-members: model_computed_fields
