import hashlib
from typing import List
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from news_summarizer.domain.chunks import ArticleChunk
from news_summarizer.domain.clean_documents import CleanedArticle


class ChunkingService:
    def __init__(
        self,
        separators: List[str],
        character_chunk_size: int = 250,
        character_chunk_overlap: int = 0,
        token_chunk_size: int = 128,
        token_chunk_overlap: int = 25,
        token_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """
        Initializes the ChunkingService with configuration parameters.

        Args:
            separators (List[str]): List of separators for character-based splitting.
            character_chunk_size (int): Size of chunks for character splitting.
            character_chunk_overlap (int): Overlap between character chunks.
            token_chunk_size (int): Maximum token count per chunk for token splitting.
            token_chunk_overlap (int): Overlap between token chunks.
            token_model_name (str): Name of the model for token-based splitting.
        """

        self._separators = separators
        self._character_chunk_size = character_chunk_size
        self._character_chunk_overlap = character_chunk_overlap
        self._token_chunk_size = token_chunk_size
        self._token_chunk_overlap = token_chunk_overlap
        self._token_model_name = token_model_name

        self.character_splitter = RecursiveCharacterTextSplitter(
            separators=self._separators,
            chunk_size=self._character_chunk_size,
            chunk_overlap=self._character_chunk_overlap,
        )
        self.token_splitter = SentenceTransformersTokenTextSplitter(
            chunk_overlap=self._token_chunk_overlap,
            tokens_per_chunk=self._token_chunk_size,
            model_name=self._token_model_name,
        )

    @property
    def separators(self):
        return self._separators

    @property
    def character_chunk_size(self):
        return self._character_chunk_size

    @property
    def character_chunk_overlap(self):
        return self._character_chunk_overlap

    @property
    def token_chunk_size(self):
        return self._token_chunk_size

    @property
    def token_chunk_overlap(self):
        return self._token_chunk_overlap

    @property
    def token_model_name(self):
        return self._token_model_name

    def split_text_into_chunks(self, text: str) -> List[str]:
        """
        Splits a given text into chunks based on characters and tokens.

        Args:
            text (str): The text to split into chunks.

        Returns:
            List[str]: A list of text chunks.
        """
        # Step 1: Split text into character-based chunks
        character_chunks = self.character_splitter.split_text(text)

        # Step 2: Further split character chunks into token-based chunks
        token_chunks = []
        for chunk in character_chunks:
            token_chunks.extend(self.token_splitter.split_text(chunk))

        return token_chunks

    def chunk(self, data_model: CleanedArticle) -> List[ArticleChunk]:
        """
        Converts a CleanedArticle into a list of ArticleChunks.

        Args:
            data_model (CleanedArticle): The article to chunk.

        Returns:
            List[ArticleChunk]: The list of resulting ArticleChunks.
        """
        # Generate text chunks
        text_chunks = self.split_text_into_chunks(data_model.content)

        # Convert text chunks into ArticleChunk models
        article_chunks = []
        for chunk in text_chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()
            article_chunk = ArticleChunk(
                id=UUID(chunk_id, version=4),
                title=data_model.title,
                subtitle=data_model.subtitle,
                content=chunk,
                author=data_model.author,
                publication_date=data_model.publication_date,
                url=data_model.url,
                document_id=data_model.id,
                metadata={
                    "chunk_size": self.character_chunk_size,
                    "chunk_overlap": self.token_chunk_overlap,
                },
            )
            article_chunks.append(article_chunk)

        return article_chunks
