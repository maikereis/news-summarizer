import logging
from urllib.parse import urlparse

from .article_page import BBCBrasilScraper, BandScraper, CNNBrasilScraper, G1Scraper, R7Scraper
from .base import BaseScraper

logger = logging.getLogger(__name__)


class ScraperRegistry:
    def __init__(self):
        self._scrapers = {}

    def register(self, name, scraper: BaseScraper):
        if name in self._scrapers:
            raise ValueError("Scraper '%s' is already registered.", name)

        logger.debug("Registering %s scraper", name)
        self._scrapers[name] = scraper

    def get(self, name):
        parsed_domain = urlparse(name)
        name = self._extract_netloc(parsed_domain)

        if name not in self._scrapers:
            raise KeyError("Scraper for '%s' not found." % name)
        return self._scrapers[name]()

    def _extract_netloc(self, domain):
        return f"{domain.scheme}://{domain.netloc}/"

    def list_scrapers(self):
        return list(self._scrapers.keys())


scraper_registry = ScraperRegistry()
scraper_registry.register("https://g1.globo.com/", G1Scraper)
scraper_registry.register("https://bandnewstv.uol.com.br/", BandScraper)
scraper_registry.register("https://noticias.r7.com/", R7Scraper)
scraper_registry.register("https://www.bbc.com/", BBCBrasilScraper)
scraper_registry.register("https://www.cnnbrasil.com.br/", CNNBrasilScraper)
