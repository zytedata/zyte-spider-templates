from logging import getLogger
from typing import Any, List, Optional, Type

from duplicate_url_discarder_rules import RULE_PATHS
from scrapy.settings import BaseSettings
from scrapy.utils.misc import load_object

from zyte_spider_templates import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
    IncrementalCrawlMiddleware,
    MaxRequestsPerSeedDownloaderMiddleware,
    OffsiteRequestsPerSeedMiddleware,
    OnlyFeedsMiddleware,
    TrackNavigationDepthSpiderMiddleware,
    TrackSeedsSpiderMiddleware,
)

logger = getLogger(__name__)


def _extend_module_list(settings: BaseSettings, setting: str, item: str) -> None:
    spider_modules: List[str] = settings.getlist(setting)
    if item not in spider_modules:
        spider_modules_priority = settings.getpriority(setting)
        settings.set(
            setting,
            spider_modules + [item],
            priority=spider_modules_priority,  # type: ignore[arg-type]
        )


def _replace_builtin(
    settings: BaseSettings, setting: str, builtin_cls: Type, new_cls: Type
) -> None:
    setting_value = settings[setting]
    if not setting_value:
        logger.warning(
            f"Setting {setting!r} is empty. Could not replace the built-in "
            f"{builtin_cls} entry with {new_cls}. Add {new_cls} manually to "
            f"silence this warning."
        )
        return None

    if new_cls in setting_value:
        return None
    for cls_or_path in setting_value:
        if isinstance(cls_or_path, str):
            _cls = load_object(cls_or_path)
            if _cls == new_cls:
                return None

    builtin_entry: Optional[Any] = None
    for _setting_value in (setting_value, settings[f"{setting}_BASE"]):
        if builtin_cls in _setting_value:
            builtin_entry = builtin_cls
            pos = _setting_value[builtin_entry]
            break
        for cls_or_path in _setting_value:
            if isinstance(cls_or_path, str):
                _cls = load_object(cls_or_path)
                if _cls == builtin_cls:
                    builtin_entry = cls_or_path
                    pos = _setting_value[builtin_entry]
                    break
        if builtin_entry:
            break

    if not builtin_entry:
        logger.warning(
            f"Settings {setting!r} and {setting + '_BASE'!r} are both "
            f"missing built-in entry {builtin_cls}. Cannot replace it with {new_cls}. "
            f"Add {new_cls} manually to silence this warning."
        )
        return None

    if pos is None:
        logger.warning(
            f"Built-in entry {builtin_cls} of setting {setting!r} is disabled "
            f"(None). Cannot replace it with {new_cls}. Add {new_cls} "
            f"manually to silence this warning. If you had replaced "
            f"{builtin_cls} with some other entry, you might also need to "
            f"disable that other entry for things to work as expected."
        )
        return

    settings[setting][builtin_entry] = None
    settings[setting][new_cls] = pos


# https://github.com/scrapy-plugins/scrapy-zyte-api/blob/a1d81d11854b420248f38e7db49c685a8d46d943/scrapy_zyte_api/addon.py#L12
def _setdefault(settings: BaseSettings, setting: str, cls: Type, pos: int) -> None:
    setting_value = settings[setting]
    if not setting_value:
        settings[setting] = {cls: pos}
        return None
    if cls in setting_value:
        return None
    for cls_or_path in setting_value:
        if isinstance(cls_or_path, str):
            _cls = load_object(cls_or_path)
            if _cls == cls:
                return None
    settings[setting][cls] = pos


class Addon:
    def update_settings(self, settings: BaseSettings) -> None:
        for setting, value in (
            ("CLOSESPIDER_TIMEOUT_NO_ITEM", 600),
            ("SCHEDULER_DISK_QUEUE", "scrapy.squeues.PickleFifoDiskQueue"),
            ("SCHEDULER_MEMORY_QUEUE", "scrapy.squeues.FifoMemoryQueue"),
            ("SCHEDULER_PRIORITY_QUEUE", "scrapy.pqueues.DownloaderAwarePriorityQueue"),
            (
                "ITEM_PROBABILITY_THRESHOLDS",
                {
                    "zyte_common_items.items.Article": 0.1,
                    "zyte_common_items.items.Product": 0.1,
                },
            ),
            ("DUD_LOAD_RULE_PATHS", RULE_PATHS),
        ):
            settings.set(setting, value, priority="addon")

        _extend_module_list(
            settings, "SCRAPY_POET_DISCOVER", "zyte_spider_templates.pages"
        )
        _extend_module_list(settings, "SPIDER_MODULES", "zyte_spider_templates.spiders")

        _setdefault(
            settings,
            "DOWNLOADER_MIDDLEWARES",
            MaxRequestsPerSeedDownloaderMiddleware,
            100,
        )
        _setdefault(settings, "SPIDER_MIDDLEWARES", IncrementalCrawlMiddleware, 45)
        _setdefault(
            settings, "SPIDER_MIDDLEWARES", OffsiteRequestsPerSeedMiddleware, 49
        )
        _setdefault(settings, "SPIDER_MIDDLEWARES", TrackSeedsSpiderMiddleware, 550)
        _setdefault(settings, "SPIDER_MIDDLEWARES", OnlyFeedsMiddleware, 108)
        _setdefault(
            settings, "SPIDER_MIDDLEWARES", TrackNavigationDepthSpiderMiddleware, 110
        )
        _setdefault(settings, "SPIDER_MIDDLEWARES", CrawlingLogsMiddleware, 1000)

        try:
            from scrapy.downloadermiddlewares.offsite import OffsiteMiddleware
        except ImportError:
            from scrapy.spidermiddlewares.offsite import (  # type: ignore[assignment]
                OffsiteMiddleware,
            )

            _replace_builtin(
                settings,
                "SPIDER_MIDDLEWARES",
                OffsiteMiddleware,
                AllowOffsiteMiddleware,
            )
        else:
            _replace_builtin(
                settings,
                "DOWNLOADER_MIDDLEWARES",
                OffsiteMiddleware,
                AllowOffsiteMiddleware,
            )
