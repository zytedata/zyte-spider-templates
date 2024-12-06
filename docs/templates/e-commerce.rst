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
    :exclude-members: model_computed_fields, single_input

Settings
========

The following :ref:`zyte-spider-templates settings <settings>` may be useful
for the e-commerce spider template:

:setting:`MAX_REQUESTS_PER_SEED`
    Limit the number of follow-up requests per initial URL.
