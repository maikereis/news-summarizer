"""Step for cleaning article text content."""

import logging
from typing import List

from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.documents import Article
from news_summarizer.preprocessing.text import pipeline
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def clean_articles(
    articles: Annotated[List[Article], "raw_articles"],
) -> Annotated[List[CleanedArticle], "cleaned_articles"]:
    """Clean and preprocess article text content."""
    cleaned_articles = []
    success_count = 0
    failure_count = 0

    for article in articles:
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
            cleaned_articles.append(cleaned_article)
            success_count += 1

        except Exception as exc:
            logger.error("Failed to clean article %s from %s: %s", article.id, article.url, exc)
            failure_count += 1

    metadata = {
        "cleaning_results": {
            "successful": success_count,
            "failed": failure_count,
            "success_rate": success_count / len(articles) if articles else 0,
            "status": "success" if failure_count == 0 else "partial_success",
        }
    }

    context = get_step_context()
    context.add_output_metadata(output_name="cleaned_articles", metadata=metadata)

    logger.info("Cleaned %d/%d articles successfully", success_count, len(articles))

    return cleaned_articles
