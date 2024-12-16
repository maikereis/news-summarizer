import logging
import time
from datetime import timedelta
from typing import Dict

from news_summarizer.domain.documents import Article, Link
from news_summarizer.scraper import ScraperExecutor, scraper_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def scrap_links() -> Annotated[Dict[str, str], "scrapped_links"]:
    logger.info("Starting to scrap links.")

    links = Link.bulk_find(**{})
    links_urls = [str(link.url) for link in links]

    articles = Article.bulk_find(**{})
    articles_urls = [str(link.url) for link in articles]

    links_to_scrap = set(links_urls) - set(articles_urls)

    start_time = time.time()
    executor = ScraperExecutor(scraper_registry)
    results = executor.run(links_to_scrap)
    end_time = time.time()

    elapsed_time = end_time - start_time
    elapsed_timedelta = timedelta(seconds=elapsed_time)

    logger.info("Total scraping time: %s", elapsed_timedelta)

    statuses = {link: "success" if status else "fail" for link, status in results.items()}

    metadata = {"links": statuses, "summary": {"num_links": len(statuses), "elapsed_time": str(elapsed_timedelta)}}

    context = get_step_context()
    context.add_output_metadata(output_name="scrapped_links", metadata=metadata)

    return metadata
