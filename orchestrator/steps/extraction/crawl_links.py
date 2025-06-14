"""Step for crawling news website links."""

import logging
import time
from datetime import timedelta
from typing import Dict

from news_summarizer.web import CrawlerExecutor, crawler_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def crawl_links(newspaper_urls: list[str]) -> Annotated[Dict[str, str], "crawled_links"]:
    """Crawl news websites to extract article links."""
    logger.info("Starting link crawling for %d websites", len(newspaper_urls))

    start_time = time.time()
    executor = CrawlerExecutor(crawler_registry)
    results = executor.run(newspaper_urls)
    elapsed_time = timedelta(seconds=time.time() - start_time)

    logger.info("Link crawling completed in %s", elapsed_time)

    statuses = {url: "success" if status else "failed" for url, status in results.items()}

    metadata = {
        "links": statuses,
        "summary": {
            "total_websites": len(statuses),
            "successful": sum(1 for s in statuses.values() if s == "success"),
            "elapsed_time": str(elapsed_time),
        },
    }

    context = get_step_context()
    context.add_output_metadata(output_name="crawled_links", metadata=metadata)

    return metadata
