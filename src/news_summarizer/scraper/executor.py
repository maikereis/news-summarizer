import logging
import time
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
        self.start_time = None
        self.scraped_count = 0

    def run(self, links: List[str]) -> Dict[str, bool]:
        results = {}
        self.start_time = time.time()  # Record the start time

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._task_wrapper, self._run_scraper, link): link for link in links}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    result = future.result()
                    results[link] = result
                    if result:
                        self.scraped_count += 1
                    self._log_scrap_rate()
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

    def _log_scrap_rate(self):
        current_time = time.time()
        duration = current_time - self.start_time  # Calculate the duration in seconds
        scrap_rate = self.scraped_count / (duration / 60)  # Calculate the scrap rate (articles per minute)
        logger.info("Current scrap rate: %.2f articles per minute", scrap_rate)
