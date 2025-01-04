import logging
from typing import List, Union

from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.embeddeg_chunks import EmbeddedArticleChunk
from news_summarizer.utils import batch
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step
def store(embedded_documents: Annotated[list, "embedded_documents"]) -> Annotated[bool, "successful"]:
    try:
        for batched_embedded_documents in batch(embedded_documents, 10):
            store_all_vectors(batched_embedded_documents)
    except Exception:
        logger.error("Error trying to iterate over chunks.")
        return False

    metadata = {"num_embedded_documents": len(embedded_documents)}
    context = get_step_context()
    context.add_output_metadata(output_name="successful", metadata=metadata)
    return True


# SomeType can be CleanedArticle or EmbeddedArticleChunk
def store_all_vectors(embedded_documents: List[Union[CleanedArticle, EmbeddedArticleChunk]]):
    if isinstance(embedded_documents[0], CleanedArticle):
        CleanedArticle.bulk_insert(embedded_documents)
    elif isinstance(embedded_documents[0], EmbeddedArticleChunk):
        EmbeddedArticleChunk.bulk_insert(embedded_documents)
    else:
        raise ValueError("Unsupported document type")
