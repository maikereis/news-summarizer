import logging
import time
from datetime import timedelta
from typing import Dict

from news_summarizer.crawler import CrawlerExecutor, crawler_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def crawl_links(newspapers_urls: list[str]) -> Annotated[Dict[str, str], "crawled_links"]:
    logger.info("Starting to crawl links.")

    start_time = time.time()
    executor = CrawlerExecutor(crawler_registry)
    results = executor.run(newspapers_urls)
    end_time = time.time()

    elapsed_time = end_time - start_time
    elapsed_timedelta = timedelta(seconds=elapsed_time)

    logger.info("Total crawling time: %s", elapsed_timedelta)

    statuses = {link: "success" if status else "fail" for link, status in results.items()}

    # Organize metadata
    metadata = {"links": statuses, "summary": {"num_links": len(statuses), "elapsed_time": str(elapsed_timedelta)}}

    context = get_step_context()
    context.add_output_metadata(output_name="crawled_links", metadata=metadata)

    return metadata
