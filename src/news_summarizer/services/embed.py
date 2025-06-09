from typing import List, Union

from news_summarizer.domain.chunks import ArticleChunk
from news_summarizer.domain.embedded_chunks import EmbeddedArticleChunk


class EmbedderService:
    def __init__(self, embedder):
        """
        Initializes the EmbedderService with the embedding model.

        Args:
            embedder: An embedding model instance with attributes like `model_id` and a callable for generating embeddings.
        """
        self.embedder = embedder

    def create_embedded_chunk(self, data_model: ArticleChunk, embedding: List[float]) -> EmbeddedArticleChunk:
        """
        Creates an EmbeddedArticleChunk from a given ArticleChunk and its embedding.
        """
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
        """
        Embeds a batch of ArticleChunks into EmbeddedArticleChunks.
        """
        embedding_inputs = [chunk.content for chunk in data_models]
        embeddings = self.embedder(embedding_inputs, to_list=True)
        return [
            self.create_embedded_chunk(chunk, embedding)
            for chunk, embedding in zip(data_models, embeddings, strict=False)
        ]

    def embed(
        self, data_model: Union[ArticleChunk, List[ArticleChunk]]
    ) -> Union[EmbeddedArticleChunk, List[EmbeddedArticleChunk]]:
        """
        Embeds one or more ArticleChunks.
        """
        is_single_instance = not isinstance(data_model, list)
        data_models = [data_model] if is_single_instance else data_model
        embedded_chunks = self.embed_batch(data_models)
        return embedded_chunks[0] if is_single_instance else embedded_chunks
