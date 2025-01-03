from datetime import datetime
from typing import Optional

from pydantic import UUID4, AnyUrl, Field, field_serializer

from .base import VectorBaseDocument


class ArticleChunk(VectorBaseDocument):
    title: str = Field(..., description="The title of the link")
    subtitle: Optional[str] = Field(..., description="The subtitle of the link")
    author: Optional[str] = Field(..., description="The author")
    publication_date: Optional[datetime] = Field(None, description="The publication date of the link")
    content: str = Field(..., description="Content")
    url: AnyUrl = Field(description="The URL of the link")
    document_id: UUID4
    metadata: dict = Field(default_factory=dict)

    @field_serializer("url")
    def url_string(self, url: AnyUrl):
        return str(url)

    class Config:
        category = "news_article"
