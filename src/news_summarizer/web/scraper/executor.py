import logging

from ..base import BaseExecutor
from .registry import ScraperRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScraperExecutor(BaseExecutor):
    def __init__(
        self, scraper_registry: ScraperRegistry, max_concurrent_scrapers: int = 4, max_workers: int = 6
    ) -> None:
        super().__init__(scraper_registry, max_concurrent_scrapers, max_workers)

    def _run(self, link: str) -> bool:
        logger.debug("Starting scraper for link: %s", link)
        scraper = self.registry.get(link)
        if not scraper:
            logger.error("No scraper registered for link: %s", link)
            return False
        try:
            scraper.extract(link)
            logger.debug("Task success: %s", link)
            return True
        except Exception as ex:
            logger.error("Task failed: %s, %s", link, ex)
            return False
