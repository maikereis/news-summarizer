import warnings
from datetime import datetime
from uuid import uuid4

import pytest
from news_summarizer.domain.clean_documents import CleanedArticle
from pydantic import AnyUrl, ValidationError

warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")


@pytest.fixture
def mock_database(monkeypatch):
    from news_summarizer.database.qdrant import FakeQdrantClient

    fake_client = FakeQdrantClient()

    monkeypatch.setattr("news_summarizer.domain.base.vector.connection", fake_client)

    return fake_client


def test_cleaned_article_model_validation():
    # Test valid instance creation
    cleaned_article = CleanedArticle(
        id=uuid4(),
        title="Test Title",
        subtitle="Test Subtitle",
        content="Some content",
        author="Author",
        publication_date=datetime(2024, 1, 1, 12, 0),
        url="http://example.com",
    )

    assert cleaned_article.title == "Test Title"
    assert cleaned_article.subtitle == "Test Subtitle"
    assert cleaned_article.url == AnyUrl("http://example.com")
    assert cleaned_article.content == "Some content"
    assert cleaned_article.publication_date == datetime(2024, 1, 1, 12, 0)
    assert isinstance(cleaned_article.publication_date, datetime)


def test_create_cleaned_article_without_url():
    with pytest.raises(ValueError):
        CleanedArticle(title="Missing URL", content="Some content")


def test_create_cleaned_article_with_invalid_url():
    with pytest.raises(ValueError):
        CleanedArticle(title="Invalid URL", url="invalid-url", content="Some content")


def test_cleaned_article_bulk_insert(mock_database):
    articles = [
        CleanedArticle(
            title="Bulk Article 1",
            subtitle="Subtitle of Bulk Article 1",
            author="Autor 1",
            content="Content 1",
            publication_date=datetime(2024, 1, 1, 12, 0),
            url="http://bulk1.com",
        ),
        CleanedArticle(
            title="Bulk Article 2",
            subtitle="Subtitle of Bulk Article 2",
            author="Autor 2",
            content="Content 2",
            publication_date=datetime(2024, 1, 1, 12, 0),
            url="http://bulk2.com",
        ),
    ]
    success = CleanedArticle.bulk_insert(articles)
    assert success

    # Ensure all articles were inserted
    collection = mock_database.get_collection(CleanedArticle.get_collection_name())
    all_articles = list(collection.vectors.values())

    assert len(all_articles) == 2
    assert all(article["payload"]["title"] in ["Bulk Article 1", "Bulk Article 2"] for article in all_articles)


def test_cleaned_article_invalid_publication_date():
    # Test invalid `publication_date` date
    with pytest.raises(ValidationError):
        CleanedArticle(
            title="Invalid Date",
            subtitle="Invalid Date",
            author="Some author",
            url="http://example.com",
            publication_date="invalid-date",
            content="Some content",
        )
