"""Pipeline for scraping full articles from links."""

from steps.extraction import remove_duplicate_articles, scrape_articles
from zenml import pipeline


@pipeline
def scrape_news_articles():
    """Scrape full article content from collected links."""
    scrape_articles()
    remove_duplicate_articles(after="scrape_articles")
