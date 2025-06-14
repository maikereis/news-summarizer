"""Pipeline definitions for the orchestrator."""

from .article_extraction import scrape_news_articles
from .dataset_generation import generate_training_dataset
from .document_processing import process_documents
from .link_extraction import crawl_news_links

__all__ = ["crawl_news_links", "scrape_news_articles", "process_documents", "generate_training_dataset"]
