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

-   Python 3.9+

-   Scrapy 2.11+

For Zyte API features, including AI-powered parsing, you need a `Zyte API`_
subscription.

.. _Zyte API: https://docs.zyte.com/zyte-api/get-started.html

Installation
============

.. code-block:: shell

    pip install zyte-spider-templates


.. _config:

Configuration
=============

In your Scrapy project settings (usually in ``settings.py``):

#.  `Configure scrapy-poet`_.

    .. _Configure scrapy-poet: https://scrapy-poet.readthedocs.io/en/stable/intro/install.html#configuring-the-project

#.  For Zyte API features, including AI-powered parsing, :ref:`configure
    scrapy-zyte-api <scrapy-zyte-api:setup>`.

#.  Configure :class:`zyte_common_items.ZyteItemAdapter`:

    .. code-block:: python
        :caption: ``settings.py``

        from itemadapter import ItemAdapter
        from zyte_common_items import ZyteItemAdapter

        ItemAdapter.ADAPTER_CLASSES.appendleft(ZyteItemAdapter)

#.  Add the zyte-spider-templates add-on to your :setting:`ADDONS
    <scrapy:ADDONS>` setting:

    .. code-block:: python
        :caption: ``settings.py``

        ADDONS = {
            "zyte_spider_templates.Addon": 1000,
        }

For an example of a properly configured ``settings.py`` file, see `the one
in zyte-spider-templates-project`_.

.. _the one in zyte-spider-templates-project: https://github.com/zytedata/zyte-spider-templates-project/blob/main/zyte_spider_templates_project/settings.py
