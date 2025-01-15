from .article_page import (
    BBCBrasilScraper,
    BandScraper,
    CNNBrasilScraper,
    G1Scraper,
    R7Scraper,
)
from .executor import ScraperExecutor
from .registry import scraper_registry

__all__ = [
    "scraper_registry",
    "G1Scraper",
    "BandScraper",
    "R7Scraper",
    "BBCBrasilScraper",
    "CNNBrasilScraper",
    "ScraperExecutor",
]
