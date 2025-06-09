from abc import ABC
from datetime import datetime
from typing import Optional

from pydantic import UUID4, AnyUrl, Field

from .base import VectorBaseDocument


class EmbeddedArticleChunk(VectorBaseDocument, ABC):
    title: str = Field(..., description="The title of the link")
    subtitle: Optional[str] = Field(..., description="The subtitle of the link")
    author: Optional[str] = Field(..., description="The author")
    publication_date: Optional[datetime] = Field(None, description="The publication date of the link")
    content: str = Field(..., description="Content")
    url: AnyUrl = Field(description="The URL of the link")
    document_id: UUID4
    embedding: list[float] | None
    metadata: dict = Field(default_factory=dict)

    class Config:
        name = "embedded_article_chunks"

    @classmethod
    def to_context(cls, chunks: list["EmbeddedArticleChunk"]) -> str:
        context = ""
        for i, chunk in enumerate(chunks):
            context += f"""
            Chunk {i + 1}:
            Type: {chunk.__class__.__name__}
            Title: {chunk.title}
            Subtitle: {chunk.subtitle}
            Publication Date: {chunk.publication_date}
            Author: {chunk.author}
            Content: {chunk.content}\n
            """
        return context
