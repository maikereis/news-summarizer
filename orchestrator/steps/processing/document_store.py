"""Step for storing processed documents."""

import logging
from typing import List, Union

from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.embedded_chunks import EmbeddedArticleChunk
from news_summarizer.utils import batch
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


@step
def store_documents(
    documents: Annotated[List[Union[CleanedArticle, EmbeddedArticleChunk]], "documents"],
) -> Annotated[bool, "storage_success"]:
    """Store processed documents in database."""
    try:
        total_stored = 0
        for i, document_batch in enumerate(batch(documents, BATCH_SIZE)):
            _bulk_store_documents(document_batch)
            logger.info("Storing %d with %d documents", i, BATCH_SIZE)
            total_stored += len(document_batch)

        metadata = {"stored_documents": total_stored}
        context = get_step_context()
        context.add_output_metadata(output_name="storage_success", metadata=metadata)

        logger.info("Successfully stored %d documents", total_stored)
        return True

    except Exception as exc:
        logger.error("Failed to store documents: %s", exc)
        return False


def _bulk_store_documents(documents: List[Union[CleanedArticle, EmbeddedArticleChunk]]):
    """Store a batch of documents based on their type."""
    if not documents:
        return

    document_type = type(documents[0])

    if document_type == CleanedArticle:
        CleanedArticle.bulk_insert(documents)
    elif document_type == EmbeddedArticleChunk:
        EmbeddedArticleChunk.bulk_insert(documents)
    else:
        raise ValueError(f"Unsupported document type: {document_type}")
