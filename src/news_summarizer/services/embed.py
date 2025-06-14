import logging
from typing import List, Union

from news_summarizer.domain.chunks import ArticleChunk
from news_summarizer.domain.embedded_chunks import EmbeddedArticleChunk

logger = logging.getLogger(__name__)


class EmbedderService:
    """Service for embedding article chunks into vector representations.

    This service converts textual article chunks into embedded vectors using
    a specified embedding model. It supports both single-item and batch
    embedding operations.

    Attributes:
        embedder: An embedding model instance with attributes such as
            `model_id`, `embedding_size`, and `max_input_length`. The model
            must be callable and return embeddings.
    """

    def __init__(self, embedder):
        """Initializes the EmbedderService with the specified embedding model.

        Args:
            embedder: A callable embedding model instance. It should accept a
                list of texts and return a list of embeddings. The instance must
                have the following attributes:
                - model_id (str): Identifier of the embedding model.
                - embedding_size (int): Dimension of the output embeddings.
                - max_input_length (int): Maximum input length supported by the model.
        """
        self.embedder = embedder
        logger.info(
            "EmbedderService initialized with model: %s | Size: %s | Max Input Length: %s",
            getattr(embedder, "model_id", "unknown"),
            getattr(embedder, "embedding_size", "unknown"),
            getattr(embedder, "max_input_length", "unknown"),
        )

    def create_embedded_chunk(self, data_model: ArticleChunk, embedding: List[float]) -> EmbeddedArticleChunk:
        """Creates an EmbeddedArticleChunk from an ArticleChunk and its embedding.

        Args:
            data_model (ArticleChunk): The original article chunk.
            embedding (List[float]): The embedding vector representing the chunk content.

        Returns:
            EmbeddedArticleChunk: A new embedded chunk containing both the content
            and its vector representation.
        """
        logger.debug("Creating EmbeddedArticleChunk for ID: %s", data_model.id)
        return EmbeddedArticleChunk(
            id=data_model.id,
            title=data_model.title,
            subtitle=data_model.subtitle,
            author=data_model.author,
            content=data_model.content,
            url=data_model.url,
            document_id=data_model.document_id,
            embedding=embedding,
            metadata={
                "embedding_model_id": self.embedder.model_id,
                "embedding_size": self.embedder.embedding_size,
                "max_input_length": self.embedder.max_input_length,
            },
        )

    def embed_batch(self, data_models: List[ArticleChunk]) -> List[EmbeddedArticleChunk]:
        """Embeds a batch of ArticleChunks into their vector representations.

        Args:
            data_models (List[ArticleChunk]): A list of article chunks to embed.

        Returns:
            List[EmbeddedArticleChunk]: A list of EmbeddedArticleChunks, each containing
            the original content and its embedding.

        Raises:
            Warning if the input list is empty (logged, but does not raise an exception).
        """
        if not data_models:
            logger.warning("Received empty batch for embedding.")
            return []

        logger.info("Embedding batch of %d articles...", len(data_models))
        embedding_inputs = [chunk.content for chunk in data_models]
        embeddings = self.embedder(embedding_inputs, to_list=True)

        logger.debug("Generated %d embeddings.", len(embeddings))
        embedded = [
            self.create_embedded_chunk(chunk, embedding)
            for chunk, embedding in zip(data_models, embeddings, strict=False)
        ]
        logger.info("Successfully embedded %d article chunks.", len(embedded))
        return embedded

    def embed(
        self, data_model: Union[ArticleChunk, List[ArticleChunk]]
    ) -> Union[EmbeddedArticleChunk, List[EmbeddedArticleChunk]]:
        """Embeds one or more ArticleChunks.

        This method supports both single ArticleChunk objects and lists of ArticleChunks.
        The output type matches the input type.

        Args:
            data_model (Union[ArticleChunk, List[ArticleChunk]]): One or multiple
                ArticleChunk instances to embed.

        Returns:
            Union[EmbeddedArticleChunk, List[EmbeddedArticleChunk]]: The embedded chunk(s)
            corresponding to the input.

        Example:
            >>> embedder = EmbedderService(my_model)
            >>> chunk = ArticleChunk(...)
            >>> embedded = embedder.embed(chunk)

            >>> chunks = [chunk1, chunk2]
            >>> embedded_list = embedder.embed(chunks)
        """
        is_single_instance = not isinstance(data_model, list)
        data_models = [data_model] if is_single_instance else data_model

        logger.debug("Embedding %s article(s)...", "1" if is_single_instance else str(len(data_models)))
        embedded_chunks = self.embed_batch(data_models)

        if is_single_instance:
            logger.debug("Returning single embedded chunk for ID: %s", embedded_chunks[0].id)
            return embedded_chunks[0]
        else:
            logger.debug("Returning list of %d embedded chunks.", len(embedded_chunks))
            return embedded_chunks
