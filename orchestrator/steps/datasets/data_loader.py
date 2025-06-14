"""Step for loading cleaned articles for dataset generation."""

import logging
from typing import List, Optional

from news_summarizer.domain.clean_documents import CleanedArticle
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def load_cleaned_articles(max_documents: Optional[int] = None) -> Annotated[List[CleanedArticle], "cleaned_articles"]:
    """Load cleaned articles with optional limit."""
    articles = _fetch_cleaned_articles_with_limit(max_documents)

    metadata = {"loaded_articles": {"count": len(articles)}}

    context = get_step_context()
    context.add_output_metadata(output_name="cleaned_articles", metadata=metadata)

    logger.info("Loaded %d cleaned articles", len(articles))
    return articles


def _fetch_cleaned_articles_with_limit(max_documents: Optional[int] = None) -> List[CleanedArticle]:
    """Fetch cleaned articles with pagination and optional limit."""
    offset = None
    articles = []

    while True:
        batch_articles, offset = CleanedArticle.bulk_find(**{}, offset=offset)

        if max_documents is not None:
            remaining_slots = max_documents - len(articles)
            if remaining_slots <= 0:
                break
            articles.extend(batch_articles[:remaining_slots])
            if len(articles) >= max_documents:
                break
        else:
            articles.extend(batch_articles)

        if offset is None:
            break

    return articles
