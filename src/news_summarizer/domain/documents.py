from datetime import datetime
from typing import Optional

from pydantic import AnyUrl, Field, field_serializer

from .base import NoSQLBaseDocument


class Link(NoSQLBaseDocument):
    title: str = Field(..., description="The title of the link")
    url: AnyUrl = Field(description="The URL of the link")
    source: Optional[str] = Field(None, description="The source of the link")
    published_at: Optional[datetime] = Field(None, description="The publication date of the link")
    extracted_at: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp when the link was extracted",
    )

    @field_serializer("url")
    def url_string(self, url: AnyUrl):
        return str(url)

    class Config:
        name = "link"


class Article(NoSQLBaseDocument):
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
        name = "article"
