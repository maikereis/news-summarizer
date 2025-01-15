import logging

from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.preprocessing.text import pipeline
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def clean(
    documents: Annotated[list, "raw_documents"],
) -> Annotated[list, "cleaned_documents"]:
    success_count = 0
    failure_count = 0

    cleaned_documents = []
    for article in documents:
        try:
            cleaned_article = CleanedArticle(
                id=article.id,
                title=pipeline.execute(article.title),
                author=article.author,
                content=pipeline.execute(article.content),
                subtitle=pipeline.execute(article.subtitle),
                publication_date=article.publication_date,
                url=article.url,
            )
            cleaned_documents.append(cleaned_article)
            success_count += 1
        except Exception:
            logger.error(
                "Error trying to clean the content of article %s from %s.",
                article.id,
                article.url,
            )
            failure_count += 1
            continue

    metadata = {
        "cleaned_documents": {
            "success_count": success_count,
            "failure_count": failure_count,
            "status": "success" if failure_count == 0 else "partial_success",
        }
    }

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="cleaned_documents", metadata=metadata)

    return cleaned_documents
