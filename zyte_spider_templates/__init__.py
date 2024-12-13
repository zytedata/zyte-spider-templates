from importlib.metadata import version
from logging import getLogger

from .spiders.base import BaseSpider, BaseSpiderParams
from .spiders.ecommerce import EcommerceSpider
from .spiders.serp import GoogleSearchSpider

logger = getLogger(__name__)
package = "zyte-spider-templates"
logger.info(f"Running {package} {version(package)}")
