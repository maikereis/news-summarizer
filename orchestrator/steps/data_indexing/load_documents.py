import logging

from news_summarizer.domain.documents import Article
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def load() -> Annotated[list, "raw_documents"]:
    articles = fetch_all_articles()

    num_articles = len(articles)

    metadata = {"num_articles": num_articles}

    context = get_step_context()
    context.add_output_metadata(output_name="raw_documents", metadata=metadata)

    return articles


def fetch_all_articles():
    return Article.bulk_find(**{})
