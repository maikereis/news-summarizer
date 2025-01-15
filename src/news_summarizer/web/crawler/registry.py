import logging

from ..base import BaseRegistry
from .newspaper_website import BBCBrasilCrawler, BandCrawler, CNNBrasilCrawler, G1Crawler, R7Crawler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CrawlerRegistry now inherits from BaseRegistry
class CrawlerRegistry(BaseRegistry):
    pass


crawler_registry = CrawlerRegistry()

crawler_registry.register("https://g1.globo.com/", G1Crawler)
crawler_registry.register("https://bandnewstv.uol.com.br/", BandCrawler)
crawler_registry.register("https://noticias.r7.com/", R7Crawler)
crawler_registry.register("https://www.bbc.com/", BBCBrasilCrawler)
crawler_registry.register("https://www.cnnbrasil.com.br/", CNNBrasilCrawler)
