import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
from typing import Callable, Dict, List, Type
from urllib.parse import urlparse

# Assuming RateCalculator is abstract and does not mix other responsibilities
from news_summarizer.utils import RateCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Abstract BaseRegistry class to handle the core logic
class BaseRegistry:
    def __init__(self):
        self._components: Dict[str, Type] = {}

    def register(self, name: str, component: Type) -> None:
        if name in self._components:
            raise ValueError(f"Component '{name}' is already registered.")

        logger.debug("Registering component: %s", name)
        self._components[name] = component

    def get(self, name: str):
        parsed_domain = urlparse(name)
        netloc = self._extract_netloc(parsed_domain)

        if netloc not in self._components:
            raise KeyError(f"Component for '{name}' not found.")
        return self._components[netloc]()

    def _extract_netloc(self, domain):
        return f"{domain.scheme}://{domain.netloc}/"

    def list_components(self):
        return list(self._components.keys())


# Interface for any kind of executor
class BaseExecutor(RateCalculator):
    def __init__(self, registry, max_concurrent: int, max_workers: int) -> None:
        self.registry = registry
        self.semaphore = Semaphore(max_concurrent)
        self.max_workers = max_workers
        self._start_time = None
        self._counter = None

    def run(self, links: List[str]) -> Dict[str, bool]:
        results = {}
        self._start_time = time.time()
        self._counter = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._task_wrapper, self._run, link): link for link in links}

            for future in as_completed(futures):
                link = futures[future]
                try:
                    result = future.result()
                    results[link] = result

                    self._counter += 1
                    rate = self._calculate_rate()
                    logger.info("Current rate: %.2f tasks/minute", rate)

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

    def _run(self, link: str) -> bool:
        raise NotImplementedError
