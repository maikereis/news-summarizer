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
def scrap_articles() -> Annotated[Dict[str, str], "scrapped_articles"]:
    logger.info("Starting to scrap links.")
    articles_to_scrap = _get_not_scraped_links()
    start_time = time.time()
    executor = ScraperExecutor(scraper_registry)
    results = executor.run(articles_to_scrap)
    end_time = time.time()

    elapsed_time = end_time - start_time
    elapsed_timedelta = timedelta(seconds=elapsed_time)

    logger.info("Total scraping time: %s", elapsed_timedelta)

    statuses = {article: "success" if status else "fail" for article, status in results.items()}

    metadata = {
        "articles": statuses,
        "summary": {"num_articles": len(statuses), "elapsed_time": str(elapsed_timedelta)},
    }

    context = get_step_context()
    context.add_output_metadata(output_name="scrapped_articles", metadata=metadata)

    return metadata


def _get_not_scraped_links(max_articles=2000):
    links_urls = [str(link.url) for link in Link.bulk_find(**{})]
    articles_urls = [str(link.url) for link in Article.bulk_find(**{})]

    not_scraped_links = list(set(links_urls) - set(articles_urls))[:max_articles]

    return not_scraped_links
