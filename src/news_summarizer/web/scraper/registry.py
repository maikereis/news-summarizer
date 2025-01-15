import logging

from ..base import BaseRegistry
from .article_page import BBCBrasilScraper, BandScraper, CNNBrasilScraper, G1Scraper, R7Scraper

logger = logging.getLogger(__name__)


# ScraperRegistry now inherits from BaseRegistry
class ScraperRegistry(BaseRegistry):
    pass


scraper_registry = ScraperRegistry()
scraper_registry.register("https://g1.globo.com/", G1Scraper)
scraper_registry.register("https://bandnewstv.uol.com.br/", BandScraper)
scraper_registry.register("https://noticias.r7.com/", R7Scraper)
scraper_registry.register("https://www.bbc.com/", BBCBrasilScraper)
scraper_registry.register("https://www.cnnbrasil.com.br/", CNNBrasilScraper)
