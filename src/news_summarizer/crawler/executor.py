import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List

from .registry import CrawlerRegistry

logger = logging.getLogger(__name__)


class CrawlerExecutor:
    def __init__(self, crawler_registry: CrawlerRegistry):
        self.crawler_registry = crawler_registry

    def run(self, links: List[str]) -> Dict[str, bool]:
        results = {}
        with ThreadPoolExecutor(max_workers=len(links)) as executor:
            # Map each link to its corresponding crawler using the registry
            futures = {executor.submit(self._run_crawler, link): link for link in links}
            for future in as_completed(futures):
                link = futures[future]
                try:
                    future.result()  # Wait for the crawler to complete
                    results[link] = True
                except Exception as e:
                    logger.error("Error occurred during crawling: %s", e)
                    results[link] = False
        return results

    def _run_crawler(self, link: str):
        logger.info("Starting crawler for link: %s", link)

        # Use the registry to select the appropriate crawler based on the link
        crawler = self.crawler_registry.get(link)
        if not crawler:
            logger.error("No crawler registered for link: %s", link)
            return

        crawler.search(link)
        logger.info("Finished crawling for link: %s", link)
