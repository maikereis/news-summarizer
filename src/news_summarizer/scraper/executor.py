import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from typing import Callable, Dict, List

from .registry import ScraperRegistry

logger = logging.getLogger(__name__)


class ScraperExecutor:
    def __init__(
        self,
        scraper_registry: "ScraperRegistry",
        max_concurrent_scrapers: int = 2,
        max_workers: int = 6,
    ):
        self.scraper_registry = scraper_registry
        self.semaphore = Semaphore(max_concurrent_scrapers)
        self.max_workers = max_workers

    def run(self, links: List[str]) -> Dict[str, bool]:
        results = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._task_wrapper, self._run_scraper, link): link for link in links}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    results[link] = future.result()
                    logger.debug("Task completed with result: %s", results[link])
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

    def _run_scraper(self, link: str) -> bool:
        logger.debug("Starting scraper for link: %s", link)

        scraper = self.scraper_registry.get(link)
        if not scraper:
            logger.error("No scraper registered for link: %s", link)
            return False

        try:
            scraper.extract(link)
            logger.debug("Finished scraping for link: %s", link)
            return True
        except Exception as e:
            logger.error("Error while scraping link %s: %s", link, e)
            return False
