import logging

from news_summarizer.domain.documents import Link
from news_summarizer.scraper import ScraperExecutor, scraper_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def scrap_links() -> Annotated[list[str], "scraped_links"]:
    logger.info("Starting to scrap links.")

    links = Link.bulk_find(**{})
    links = [str(link.url) for link in links]

    executor = ScraperExecutor(scraper_registry)

    metadata = executor.run(links)

    context = get_step_context()
    context.add_output_metadata(output_name="scraped_links", metadata=metadata)

    return list(metadata.values())
