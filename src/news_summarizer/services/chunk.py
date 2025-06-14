import hashlib
import logging
from typing import List
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
from news_summarizer.domain.chunks import ArticleChunk
from news_summarizer.domain.clean_documents import CleanedArticle

logger = logging.getLogger(__name__)


class ChunkingService:
    """Service for splitting articles into manageable text chunks.

    This class provides functionality to split text into smaller pieces
    (chunks) using a combination of character-based and token-based splitting.
    It supports multilingual tokenization via a SentenceTransformers model.

    The service is primarily designed to process cleaned news articles into
    structured chunks suitable for embedding, storage, or downstream tasks
    like retrieval or summarization.

    Attributes:
        separators (List[str]): List of separators for character-based splitting.
        character_chunk_size (int): Maximum size (in characters) for character-based chunks.
        character_chunk_overlap (int): Number of overlapping characters between consecutive chunks.
        token_chunk_size (int): Maximum number of tokens per token-based chunk.
        token_chunk_overlap (int): Number of overlapping tokens between consecutive token-based chunks.
        token_model_name (str): Hugging Face model name for token-based splitting.
    """

    def __init__(
        self,
        separators: List[str],
        character_chunk_size: int = 250,
        character_chunk_overlap: int = 0,
        token_chunk_size: int = 128,
        token_chunk_overlap: int = 25,
        token_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ):
        """Initializes the ChunkingService with the specified parameters.

        Args:
            separators (List[str]): List of separators used for character-based splitting.
            character_chunk_size (int, optional): Maximum number of characters per chunk.
                Defaults to 250.
            character_chunk_overlap (int, optional): Number of overlapping characters between
                character-based chunks. Defaults to 0.
            token_chunk_size (int, optional): Maximum number of tokens per token-based chunk.
                Defaults to 128.
            token_chunk_overlap (int, optional): Number of overlapping tokens between
                token-based chunks. Defaults to 25.
            token_model_name (str, optional): Hugging Face model name for tokenization.
                Defaults to "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2".
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

        logger.info(
            "ChunkingService initialized with: char_size=%d, char_overlap=%d, token_size=%d, token_overlap=%d, model='%s'",
            character_chunk_size,
            character_chunk_overlap,
            token_chunk_size,
            token_chunk_overlap,
            token_model_name,
        )

    @property
    def separators(self) -> list[str]:
        return self._separators

    @property
    def character_chunk_size(self) -> int:
        return self._character_chunk_size

    @property
    def character_chunk_overlap(self) -> int:
        return self._character_chunk_overlap

    @property
    def token_chunk_size(self) -> int:
        return self._token_chunk_size

    @property
    def token_chunk_overlap(self) -> int:
        return self._token_chunk_overlap

    @property
    def token_model_name(self) -> str:
        return self._token_model_name

    def split_text_into_chunks(self, text: str) -> List[str]:
        """Splits raw text into manageable chunks using character and token boundaries.

        The method first applies character-based splitting using predefined separators.
        Then, each character chunk is further split into token-based chunks to ensure
        that token limits are respected.

        Args:
            text (str): The input text to split.

        Returns:
            List[str]: A list of text chunks.
        """
        # Step 1: Split text into character-based chunks
        character_chunks = self.character_splitter.split_text(text)
        logger.debug("Character-based splitting produced %d chunks", len(character_chunks))

        # Step 2: Further split character chunks into token-based chunks
        token_chunks = []
        for i, chunk in enumerate(character_chunks):
            chunk_tokens = self.token_splitter.split_text(chunk)
            logger.debug("Chunk %d split into %d token-based chunks", i + 1, len(chunk_tokens))
            token_chunks.extend(chunk_tokens)

        logger.info("Total token-based chunks produced: %d", len(token_chunks))
        return token_chunks

    def chunk(self, data_model: CleanedArticle) -> List[ArticleChunk]:
        """Converts a CleanedArticle object into a list of ArticleChunks.

        This method generates unique chunk IDs using an MD5 hash of the chunk content,
        and attempts to format it as a UUID. Each chunk retains metadata from the original
        article (such as title, author, and URL) along with chunk-specific metadata.

        Args:
            data_model (CleanedArticle): The article to be chunked.

        Returns:
            List[ArticleChunk]: A list of ArticleChunk objects containing chunked content
            and associated metadata.
        """
        # Generate text chunks
        logger.info("Chunking article: %s", data_model.title)
        text_chunks = self.split_text_into_chunks(data_model.content)

        # Convert text chunks into ArticleChunk models
        article_chunks = []
        for chunk in text_chunks:
            chunk_id = hashlib.md5(chunk.encode()).hexdigest()

            try:
                chunk_uuid = UUID(chunk_id[:32], version=4)  # ensure valid UUID
            except ValueError:
                logger.warning("Failed to convert hash to UUID: %s", chunk_id)
                continue

            article_chunk = ArticleChunk(
                id=chunk_uuid,
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

        logger.info("Created %d article chunks for article ID: %s", len(article_chunks), data_model.id)
        return article_chunks
