from importlib.metadata import version
from logging import getLogger

from ._incremental.middleware import IncrementalCrawlMiddleware
from .middlewares import (
    AllowOffsiteMiddleware,
    CrawlingLogsMiddleware,
    MaxRequestsPerSeedDownloaderMiddleware,
    OffsiteRequestsPerSeedMiddleware,
    OnlyFeedsMiddleware,
    TrackNavigationDepthSpiderMiddleware,
    TrackSeedsSpiderMiddleware,
)
from .spiders.article import ArticleSpider
from .spiders.base import BaseSpider, BaseSpiderParams
from .spiders.ecommerce import EcommerceSpider
from .spiders.job_posting import JobPostingSpider
from .spiders.serp import GoogleSearchSpider

from ._addon import Addon  # isort: skip

logger = getLogger(__name__)
package = "zyte-spider-templates"
logger.info(f"Running {package} {version(package)}")
