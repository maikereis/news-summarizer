"""Step for scraping article content."""

import logging
import time
from datetime import timedelta
from typing import Dict

from news_summarizer.domain.documents import Article, Link
from news_summarizer.web import ScraperExecutor, scraper_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def scrape_articles() -> Annotated[Dict[str, str], "scraped_articles"]:
    """Scrape full content from article links."""
    articles_to_scrape = _get_unscraped_links()
    logger.info("Starting to scrape %d articles", len(articles_to_scrape))

    start_time = time.time()
    executor = ScraperExecutor(scraper_registry)
    results = executor.run(articles_to_scrape)
    elapsed_time = timedelta(seconds=time.time() - start_time)

    logger.info("Article scraping completed in %s", elapsed_time)

    statuses = {url: "success" if status else "failed" for url, status in results.items()}

    metadata = {
        "articles": statuses,
        "summary": {
            "total_articles": len(statuses),
            "successful": sum(1 for s in statuses.values() if s == "success"),
            "elapsed_time": str(elapsed_time),
        },
    }

    context = get_step_context()
    context.add_output_metadata(output_name="scraped_articles", metadata=metadata)

    return metadata


def _get_unscraped_links(max_articles: int = 2000) -> list[str]:
    """Get links that haven't been scraped yet."""
    link_urls = {str(link.url) for link in Link.bulk_find(**{})}
    article_urls = {str(article.url) for article in Article.bulk_find(**{})}

    unscraped = list(link_urls - article_urls)[:max_articles]
    return unscraped
