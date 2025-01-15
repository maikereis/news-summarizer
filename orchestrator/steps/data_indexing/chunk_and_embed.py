import logging

from news_summarizer.embeddings import EmbeddingModel
from news_summarizer.services.chunk import ChunkingService
from news_summarizer.services.embed import EmbedderService
from news_summarizer.utils import batch, device_selector
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)

BRAZILLIAN_PORTUGUESE_SEPARATORS = [
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
def vectorize(
    cleaned_documents: Annotated[list, "cleaned_documents"],
) -> Annotated[list, "embedded_documents"]:
    embedder = EmbeddingModel(device=device_selector(), cache_dir=None)
    chunking_service = ChunkingService(separators=BRAZILLIAN_PORTUGUESE_SEPARATORS)
    embedder_service = EmbedderService(embedder)

    chunking_success_count = 0
    chunking_failure_count = 0
    embedding_success_count = 0
    embedding_failure_count = 0

    embedded_chunks = []
    for document in cleaned_documents:
        try:
            chunks = chunking_service.chunk(document)
            chunking_success_count += 1
        except Exception:
            logger.error("Error trying to chunk document %s from %s", document.id, document.url)
            chunking_failure_count += 1
            continue

        try:
            for batched_chunks in batch(chunks, 50):
                try:
                    batched_embedded_chunks = embedder_service.embed(batched_chunks)
                    embedded_chunks.extend(batched_embedded_chunks)
                    embedding_success_count += 50
                except Exception:
                    logger.error("Error trying to embed document chunks.")
                    embedding_failure_count += 50
        except Exception:
            logger.error("Error trying to iterate over chunks.")
            embedding_failure_count += 50

    metadata = {
        "chunking": {
            "chunking_token_model_name": chunking_service.token_model_name,
            "chunking_separators": repr(chunking_service.separators),
            "chunking_character_chunk_size": chunking_service.character_chunk_size,
            "chunking_character_chunk_overlap": chunking_service.character_chunk_overlap,
            "chunking_token_chunk_size": chunking_service.token_chunk_size,
            "chunking_token_chunk_overlap": chunking_service.token_chunk_overlap,
            "success_count": chunking_success_count,
            "failure_count": chunking_failure_count,
            "status": "success" if chunking_failure_count == 0 else "partial_success",
        },
        "embedding": {
            "embedding_model_id": embedder.model_id,
            "embedding_zize": embedder.embedding_size,
            "embedding_max_input_size": embedder.max_input_length,
            "success_count": embedding_success_count,
            "failure_count": embedding_failure_count,
            "status": "success" if embedding_failure_count == 0 else "partial_success",
        },
    }

    context = get_step_context()
    context.add_output_metadata(output_name="embedded_documents", metadata=metadata)

    return embedded_chunks
