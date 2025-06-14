"""Step for loading raw articles from database."""

import logging
from typing import List

from news_summarizer.domain.documents import Article
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def load_articles() -> Annotated[List[Article], "raw_articles"]:
    """Load all raw articles from database."""
    articles = Article.bulk_find(**{})

    metadata = {"loaded_articles": {"count": len(articles)}}

    context = get_step_context()
    context.add_output_metadata(output_name="raw_articles", metadata=metadata)

    logger.info("Loaded %d raw articles", len(articles))

    return articles
