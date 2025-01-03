import hashlib
from typing import List
from uuid import UUID

from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter

from news_summarizer.domain.chunks import ArticleChunk
from news_summarizer.domain.clean_documents import CleanedArticle

separators = [
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


def chunk_text(text: str, chunk_size: int = 250, chunk_overlap: int = 25) -> List[str]:
    character_splitter = RecursiveCharacterTextSplitter(separators=separators, chunk_size=chunk_size, chunk_overlap=0)
    text_split_by_characters = character_splitter.split_text(text)

    token_splitter = SentenceTransformersTokenTextSplitter(
        chunk_overlap=chunk_overlap,
        tokens_per_chunk=128,
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",  #'sentence-transformers/all-MiniLM-L6-v2',
    )
    chunks_by_tokens = []
    for section in text_split_by_characters:
        chunks_by_tokens.extend(token_splitter.split_text(section))

    return chunks_by_tokens


def chunk_article(data_model: CleanedArticle) -> List[ArticleChunk]:
    data_models_list = []

    chunks = chunk_text(data_model.content, chunk_size=250, chunk_overlap=25)

    for chunk in chunks:
        chunk_id = hashlib.md5(chunk.encode()).hexdigest()
        model = ArticleChunk(
            id=UUID(chunk_id, version=4),
            title=data_model.title,
            subtitle=data_model.subtitle,
            content=chunk,
            author=data_model.author,
            publication_date=data_model.publication_date,
            url=data_model.url,
            metadata={"chunk_size": 250, "chunk_overlap": 25},
        )
        data_models_list.append(model)
    return data_models_list
