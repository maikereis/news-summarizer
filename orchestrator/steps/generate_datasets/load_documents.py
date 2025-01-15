import logging

from news_summarizer.domain.clean_documents import CleanedArticle
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def load() -> Annotated[list, "cleaned_documents"]:
    clean_articles = _fetch_all_cleaned_articles()

    metadata = {"loaded_documents": {"num_documents": len(clean_articles)}}

    context = get_step_context()
    context.add_output_metadata(output_name="cleaned_documents", metadata=metadata)

    return clean_articles


def _fetch_all_cleaned_articles():
    offset = None
    documents = []

    while True:
        articles, offset = CleanedArticle.bulk_find(**{}, offset=offset)
        documents.extend(articles)

        if offset is None:
            break

    return documents
