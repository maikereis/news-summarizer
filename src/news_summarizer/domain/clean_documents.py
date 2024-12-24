from datetime import datetime
from typing import Optional

from pydantic import AnyUrl, Field, field_serializer

from .base import VectorBaseDocument


class CleanedArticle(VectorBaseDocument):
    title: str = Field(..., description="The title of the link")
    subtitle: Optional[str] = Field(..., description="The subtitle of the link")
    author: Optional[str] = Field(..., description="The author")
    publication_date: Optional[datetime] = Field(None, description="The publication date of the link")
    content: str = Field(..., description="Content")
    url: AnyUrl = Field(description="The URL of the link")

    @field_serializer("url")
    def url_string(self, url: AnyUrl):
        return str(url)

    class Config:
        name = "cleaned_articles"
        category = "news_article"
        use_vector_index = False
