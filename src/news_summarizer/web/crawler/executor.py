import logging

from ..base import BaseExecutor
from .registry import CrawlerRegistry

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


# CrawlerExecutor now only focuses on running the crawler tasks
class CrawlerExecutor(BaseExecutor):
    def __init__(
        self, crawler_registry: CrawlerRegistry, max_concurrent_crawlers: int = 4, max_workers: int = 6
    ) -> None:
        super().__init__(crawler_registry, max_concurrent_crawlers, max_workers)

    def _run(self, link: str) -> bool:
        logger.info("Starting crawler for link: %s", link)
        crawler = self.registry.get(link)
        if not crawler:
            logger.error("No crawler registered for link: %s", link)
            return False
        try:
            crawler.search(link)
            logger.debug("Task success: %s", link)
            return True
        except Exception as ex:
            logger.error("Task failed: %s, %s", link, err)
            return False
