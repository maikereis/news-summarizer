import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from typing import Callable, Dict, List

from .registry import CrawlerRegistry

logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)


class CrawlerExecutor:
    def __init__(
        self,
        crawler_registry: "CrawlerRegistry",
        max_concurrent_crawlers: int = 2,
        max_workers: int = 6,
    ):
        self.crawler_registry = crawler_registry
        self.semaphore = Semaphore(max_concurrent_crawlers)
        self.max_workers = max_workers

    def run(self, links: List[str]) -> Dict[str, bool]:
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._task_wrapper, self._run_crawler, link): link for link in links}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    result = future.result()
                    results[link] = result
                    logger.debug("Task completed with result: %s", result)
                except Exception as e:
                    logger.error("Error occurred during task execution: %s", e)
                    results[link] = False
        return results

    def _task_wrapper(self, function: Callable, *args, **kwargs) -> None:
        with self.semaphore:
            logger.debug("Semaphore acquired.")
            try:
                return function(*args, **kwargs)
            finally:
                logger.debug("Semaphore released.")

    def _run_crawler(self, link: str):
        logger.info("Starting crawler for link: %s", link)

        crawler = self.crawler_registry.get(link)
        if not crawler:
            logger.error("No crawler registered for link: %s", link)
            return False

        try:
            crawler.search(link)
            logger.debug("Finished crawling for link: %s", link)
            return True
        except Exception as e:
            logger.error("Error while crawling link %s: %s", link, e)
            return False
