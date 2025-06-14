"""
News Summarizer Orchestrator Module

Orchestrates ML pipelines for news data processing and summarization.
"""

from .pipelines import crawl_news_links, generate_training_dataset, process_documents, scrape_news_articles

__version__ = "1.0.0"
__all__ = ["crawl_news_links", "scrape_news_articles", "process_documents", "generate_training_dataset"]
