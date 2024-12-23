import uuid
import warnings

import pytest
from news_summarizer.domain.base.vector import VectorBaseDocument
from pydantic import Field
from qdrant_client.models import PointStruct, Record

warnings.filterwarnings("ignore", category=DeprecationWarning, module="pydantic")


@pytest.fixture
def mock_database(monkeypatch):
    from news_summarizer.database.qdrant import FakeQdrantClient

    fake_client = FakeQdrantClient()

    monkeypatch.setattr("news_summarizer.domain.base.vector.connection", fake_client)

    return fake_client


# Utility functions
def create_mock_record(id: uuid.UUID, embedding=None, payload=None):
    embedding = embedding or [0.1, 0.2, 0.3]
    payload = payload or {}
    return Record(id=str(id), vector=embedding, payload=payload)


# Mock class for testing
class MockDocument(VectorBaseDocument):
    embedding: list = Field(default_factory=[])

    class Config:
        name = "mock_collection"
        category = "mock_category"
        use_vector_index = True


# Test cases
def test_to_point():
    doc = MockDocument(id=uuid.uuid4(), embedding=[0.1, 0.2, 0.3])
    point = doc.to_point()
    assert isinstance(point, PointStruct)
    assert point.id == str(doc.id)
    assert point.vector == doc.embedding
    assert "id" not in point.payload  # Ensure 'id' is excluded from payload


def test_from_record(mock_database):
    generated_uuid = uuid.uuid4()
    record = create_mock_record(generated_uuid, [0.1, 0.2, 0.3], {"key": "value"})
    doc = MockDocument.from_record(record)

    assert isinstance(doc, MockDocument)
    assert doc.embedding == record.vector
    assert str(doc.id) == record.id


def test_bulk_insert(mock_database, monkeypatch):
    documents = [
        MockDocument(embedding=[0.3, 0.6, 0.2]),
        MockDocument(embedding=[0.4, 0.1, 0.6]),
        MockDocument(embedding=[0.2, 0.2, 0.5]),
    ]

    # Mock the EmbeddingModel to avoid initialization issues
    class MockEmbeddingModel:
        def __init__(self):
            self.embedding_size = 3

    # Monkeypatch the EmbeddingModel class
    monkeypatch.setattr("news_summarizer.domain.base.vector.EmbeddingModel", MockEmbeddingModel)

    result = MockDocument.bulk_insert(documents)
    assert result is True


def test_bulk_find(mock_database, monkeypatch):
    documents = [
        MockDocument(embedding=[0.3, 0.6, 0.2]),
        MockDocument(embedding=[0.4, 0.1, 0.6]),
        MockDocument(embedding=[0.2, 0.2, 0.5]),
        MockDocument(embedding=[0.5, 0.7, 0.2]),
        MockDocument(embedding=[0.8, 0.9, 0.3]),
        MockDocument(embedding=[0.3, 0.1, 0.8]),
    ]

    # Mock the EmbeddingModel to avoid initialization issues
    class MockEmbeddingModel:
        def __init__(self):
            self.embedding_size = 3

    # Monkeypatch the EmbeddingModel class
    monkeypatch.setattr("news_summarizer.domain.base.vector.EmbeddingModel", MockEmbeddingModel)

    result = MockDocument.bulk_insert(documents)

    assert result

    documents, next_offset = MockDocument.bulk_find(limit=3)

    assert len(documents) == 3
    assert type(next_offset) == uuid.UUID

    expected_embeddings = [0.3, 0.6, 0.2]
    assert documents[0].embedding == expected_embeddings

    documents, next_offset = MockDocument.bulk_find(limit=2, offset=next_offset)
    assert len(documents) == 2
    assert type(next_offset) == uuid.UUID
