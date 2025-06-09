import logging
from typing import List

from news_summarizer.domain.documents import Article
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def load() -> Annotated[List[Article], "raw_documents"]:
    articles = _fetch_all_articles()

    metadata = {"loaded_documents": {"num_documents": len(articles)}}

    context = get_step_context()
    context.add_output_metadata(output_name="raw_documents", metadata=metadata)

    return articles


def _fetch_all_articles():
    return Article.bulk_find(**{})
