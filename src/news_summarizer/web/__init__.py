from .crawler import (
    BandCrawler,
    CrawlerExecutor,
    G1Crawler,
    R7Crawler,
    crawler_registry,
)
from .scraper import (
    BBCBrasilScraper,
    BandScraper,
    CNNBrasilScraper,
    G1Scraper,
    R7Scraper,
    ScraperExecutor,
    scraper_registry,
)

__all__ = [
    "scraper_registry",
    "G1Scraper",
    "BandScraper",
    "R7Scraper",
    "BBCBrasilScraper",
    "CNNBrasilScraper",
    "ScraperExecutor",
    "crawler_registry",
    "G1Crawler",
    "BandCrawler",
    "R7Crawler",
    "BBCBrasilCralwer",
    "CrawlerExecutor",
]
