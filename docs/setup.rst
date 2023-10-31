=============
Initial setup
=============

Learn how to get :ref:`spider templates <spider-templates>` installed and
configured on an existing Scrapy_ project.

.. _Scrapy: https://docs.scrapy.org/en/latest/

.. tip:: If you do not have a Scrapy project yet, use
    `zyte-spider-templates-project`_ as a starting template to get started
    quickly.

.. _zyte-spider-templates-project: https://github.com/zytedata/zyte-spider-templates-project

Requirements
============

-   Python 3.8+

-   Scrapy 2.11+

For Zyte API features, including AI-powered parsing, you need a `Zyte API`_
subscription.

.. _Zyte API: https://docs.zyte.com/zyte-api/get-started.html

Installation
============

.. code-block:: shell

    pip install zyte-spider-templates


Configuration
=============

In your Scrapy project settings (usually in ``settings.py``):

-   Update :setting:`SPIDER_MODULES <scrapy:SPIDER_MODULES>` to include
    ``"zyte_spider_templates.spiders"``.

-   `Configure scrapy-poet`_, and update :ref:`SCRAPY_POET_DISCOVER
    <scrapy-poet:settings>` to include
    ``"zyte_spider_templates.page_objects"``.

    .. _Configure scrapy-poet: https://scrapy-poet.readthedocs.io/en/stable/intro/install.html#configuring-the-project

For Zyte API features, including AI-powered parsing, `configure
scrapy-zyte-api`_ with `scrapy-poet integration`_.

.. _configure scrapy-zyte-api: https://github.com/scrapy-plugins/scrapy-zyte-api#quick-start
.. _scrapy-poet integration: https://github.com/scrapy-plugins/scrapy-zyte-api#scrapy-poet-integration

The following additional settings are recommended:

-   Set :setting:`CLOSESPIDER_TIMEOUT_NO_ITEM
    <scrapy:CLOSESPIDER_TIMEOUT_NO_ITEM>` to 600, to force the spider to stop
    if no item has been found for 10 minutes.

-   Set :setting:`SCHEDULER_DISK_QUEUE <scrapy:SCHEDULER_DISK_QUEUE>` to
    ``"scrapy.squeues.PickleFifoDiskQueue"`` and
    :setting:`SCHEDULER_MEMORY_QUEUE <scrapy:SCHEDULER_MEMORY_QUEUE>` to
    ``"scrapy.squeues.FifoMemoryQueue"``, for better request scheduling
    performance.

For an example of a properly configured ``settings.py`` file, see `the one
in zyte-spider-templates-project`_.

.. _the one in zyte-spider-templates-project: https://github.com/zytedata/zyte-spider-templates-project/blob/main/zyte_spider_templates_project/settings.py
