"""Step for vectorizing article chunks."""

import logging
from typing import List

from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.embedded_chunks import EmbeddedArticleChunk
from news_summarizer.embeddings import EmbeddingModel
from news_summarizer.services.chunk import ChunkingService
from news_summarizer.services.embed import EmbedderService
from news_summarizer.utils import batch, device_selector
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)

PORTUGUESE_TEXT_SEPARATORS = [
    "\n\n",  # Paragraph breaks
    "\n",  # Line breaks
    " ",  # Spaces
    ".",  # Periods
    ",",  # Commas
    "!",  # Exclamation marks
    "?",  # Question marks
    ";",  # Semicolons
    ":",  # Colons
    "\u2026",  # Ellipsis (…)
    "\u00a0",  # Non-breaking space
]


@step
def vectorize_articles(
    cleaned_articles: Annotated[List[CleanedArticle], "cleaned_articles"],
) -> Annotated[List[EmbeddedArticleChunk], "embedded_chunks"]:
    """Chunk and vectorize cleaned articles."""
    # Initialize services
    embedder = EmbeddingModel(device=device_selector(), cache_dir=None)
    chunking_service = ChunkingService(separators=PORTUGUESE_TEXT_SEPARATORS)
    embedder_service = EmbedderService(embedder)

    # Tracking metrics
    chunking_stats = {"success": 0, "failed": 0}
    embedding_stats = {"success": 0, "failed": 0}

    embedded_chunks = []

    for article in cleaned_articles:
        # Chunk the article
        try:
            chunks = chunking_service.chunk(article)
            chunking_stats["success"] += 1
        except Exception as exc:
            logger.error("Failed to chunk article %s: %s", article.id, exc)
            chunking_stats["failed"] += 1
            continue

        # Embed chunks in batches
        try:
            for chunk_batch in batch(chunks, 50):
                try:
                    embedded_batch = embedder_service.embed(chunk_batch)
                    embedded_chunks.extend(embedded_batch)
                    embedding_stats["success"] += len(embedded_batch)
                except Exception as exc:
                    logger.error("Failed to embed chunk batch: %s", exc)
                    embedding_stats["failed"] += len(chunk_batch)

        except Exception as exc:
            logger.error("Failed to process chunks for article %s: %s", article.id, exc)
            embedding_stats["failed"] += len(chunks)

    # Prepare metadata
    metadata = {
        "chunking": {
            "model_name": chunking_service.token_model_name,
            "separators": repr(chunking_service.separators),
            "chunk_size_chars": chunking_service.character_chunk_size,
            "chunk_overlap_chars": chunking_service.character_chunk_overlap,
            "chunk_size_tokens": chunking_service.token_chunk_size,
            "chunk_overlap_tokens": chunking_service.token_chunk_overlap,
            **chunking_stats,
            "status": "success" if chunking_stats["failed"] == 0 else "partial_success",
        },
        "embedding": {
            "model_id": embedder.model_id,
            "embedding_size": embedder.embedding_size,
            "max_input_length": embedder.max_input_length,
            **embedding_stats,
            "status": "success" if embedding_stats["failed"] == 0 else "partial_success",
        },
    }

    context = get_step_context()
    context.add_output_metadata(output_name="embedded_chunks", metadata=metadata)

    logger.info(
        "Vectorization complete: %d chunks embedded, %d failed", embedding_stats["success"], embedding_stats["failed"]
    )
