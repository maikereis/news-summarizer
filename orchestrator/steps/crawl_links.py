import logging
from urllib.parse import urlparse

from news_summarizer.crawler import crawler_registry
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def crawl_links(newspapers_urls: list[str]) -> Annotated[list[str], "crawled_links"]:
    logger.info("Starting to crawl links.")

    metadata = {}

    for url in newspapers_urls:
        status, url = _crawl_link(crawler_registry, url)

        metadata = _update_metadata(metadata, url, status)

    context = get_step_context()
    context.add_output_metadata(output_name="crawled_links", metadata=metadata)

    return newspapers_urls


def _crawl_link(registry, url):
    try:
        if _is_valid_domain_url(url):
            crawler_instance = registry.get(url)
            crawler_instance.search(link=url)
            return (True, url)
    except KeyError as ke:
        logger.error("Error trying to get crawler: %s", ke)
        return (False, url)


def _is_valid_domain_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except ValueError:
        return False


def _update_metadata(metadata, url, status) -> dict:
    if url not in metadata:
        metadata[url] = {}

    metadata[url]["succesful"] = metadata.get(url, {}).get("successful", 0) + status
    metadata[url]["total"] = metadata.get(url, {}).get("total", 0) + 1

    return metadata
