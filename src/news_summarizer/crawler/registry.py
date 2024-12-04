import logging
import re

from .base import BaseCrawler
from .newspaper_website import BandCrawler, G1Crawler, R7Crawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CrawlerRegistry:
    def __init__(self):
        self._crawlers = {}

    def register(self, name, crawler: BaseCrawler):
        if name in self._crawlers:
            raise ValueError("Crawler '%s' is already registered.", name)

        logger.debug("Registering %s crawler", name)
        self._crawlers[name] = crawler

    def get(self, name):
        if name not in self._crawlers:
            raise KeyError("Crawler '%s' not found.", name)

        logger.debug("Returning %s crawler", name)
        return self._crawlers[name]

    def _extract_url(self, url):
        return r"https://(www\.)?{}/*".format(re.escape(url))

    def list_crawlers(self):
        return list(self._crawlers.keys())


crawler_registry = CrawlerRegistry()
crawler_registry.register("https://g1.globo.com/", G1Crawler)
crawler_registry.register("https://bandnewstv.uol.com.br/", BandCrawler)
crawler_registry.register("https://www.r7.com/", R7Crawler)
