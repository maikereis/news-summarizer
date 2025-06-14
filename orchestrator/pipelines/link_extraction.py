"""Pipeline for crawling and extracting news links."""

from steps.extraction import crawl_links, remove_duplicate_links
from zenml import pipeline


@pipeline
def crawl_news_links(newspaper_urls: list[str]):
    """Crawl news websites and extract article links."""
    crawl_links(newspaper_urls)
    remove_duplicate_links(after="crawl_links")
