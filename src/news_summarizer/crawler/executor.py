import logging
from concurrent.futures import ThreadPoolExecutor
from typing import List

from .registry import CrawlerRegistry

logger = logging.getLogger(__name__)


class CrawlerExecutor:
    def __init__(self, crawler_registry: CrawlerRegistry):
        self.crawler_registry = crawler_registry

    def run(self, links: List[str]):
        with ThreadPoolExecutor(max_workers=len(links)) as executor:
            # Map each link to its corresponding crawler using the registry
            futures = [executor.submit(self._run_crawler, link) for link in links]
            for future in futures:
                try:
                    future.result()  # Wait for the crawler to complete
                except Exception as e:
                    logger.error("Error occurred during crawling: %s", e)

    def _run_crawler(self, link: str):
        logger.info("Starting crawler for link: %s", link)

        # Use the registry to select the appropriate crawler based on the link
        crawler_cls = self.crawler_registry.get(link)
        if not crawler_cls:
            logger.error("No crawler registered for link: %s", link)
            return

        crawler = crawler_cls()
        crawler.search(link)
        logger.info("Finished crawling for link: %s", link)
