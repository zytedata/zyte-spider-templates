from warnings import warn

from ..pages import HeuristicsArticleNavigationPage, HeuristicsProductNavigationPage

warn(
    "The zyte_spider_templates.page_objects module is deprecated, use "
    "zyte_spider_templates.pages instead.",
    DeprecationWarning,
    stacklevel=2,
)
