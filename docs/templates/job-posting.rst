.. _job-posting:

=============================================
Job posting spider template (``job_posting``)
=============================================

Basic use
=========

.. code-block:: shell

    scrapy crawl job_posting -a url="https://books.toscrape.com"

Parameters
==========

.. autopydantic_model:: zyte_spider_templates.spiders.job_posting.JobPostingSpiderParams
    :inherited-members: BaseModel
    :exclude-members: model_computed_fields
