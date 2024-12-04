from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from news_summarizer.domain.documents import Link
from pydantic import AnyUrl, ValidationError


@pytest.fixture
def mock_database(monkeypatch):
    """
    Sets up a fake MongoDB database with a `link` collection and monkeypatches it.
    """
    from news_summarizer.database.mongo import FakeMongoClient

    # Set up fake database
    fake_client = FakeMongoClient()
    _database = fake_client["test_database"]
    monkeypatch.setattr("news_summarizer.domain.base.nosql._database", _database)

    # Clear and prepare the collection
    _database["link"].data.clear()

    return _database


def test_link_model_validation():
    # Test valid instance creation
    link = Link(
        id=uuid4(),
        title="Test Title",
        url="http://example.com",
        source="Test Source",
        published_at=datetime(2024, 1, 1, 12, 0),
    )

    assert link.title == "Test Title"
    assert link.url == AnyUrl("http://example.com")
    assert link.source == "Test Source"
    assert link.published_at == datetime(2024, 1, 1, 12, 0)
    assert isinstance(link.extracted_at, datetime)


def test_create_link_whitout_url():
    with pytest.raises(ValueError):
        Link(title="Missing URL")


def test_create_link_with_invalid_url():
    with pytest.raises(ValueError):
        Link(title="Invalid URL", url="invalid-url")


def test_link_save(mock_database):
    # Save a new link to the mock database
    link = Link(title="Sample Link", url="http://example.com")
    saved_link = link.save()

    # Ensure it was saved correctly
    collection = mock_database["link"]
    found_link = collection.find_one({"_id": str(saved_link.id)})

    assert found_link is not None
    assert found_link["title"] == "Sample Link"
    assert found_link["url"] == "http://example.com/"


def test_link_get_or_create(mock_database):
    # Create a new link
    link = Link.get_or_create(title="New Link", url="http://example.com")
    link_uuid = link.id

    # Ensure the link was saved
    collection = mock_database["link"]
    found_link = collection.find_one({"_id": str(link_uuid)})

    assert found_link is not None
    assert found_link["title"] == "New Link"
    assert found_link["url"] == "http://example.com/"

    # Retrieve the same link without creating a new one
    same_link = Link.get_or_create(title="New Link", url="http://example.com/")
    assert same_link.id == link_uuid


def test_link_bulk_insert(mock_database):
    links = [
        Link(title="Bulk Link 1", url="http://bulk1.com"),
        Link(title="Bulk Link 2", url="http://bulk2.com"),
    ]
    success = Link.bulk_insert(links)
    assert success

    # Ensure all links were inserted
    collection = mock_database["link"]
    all_links = list(collection.data.values())

    assert len(all_links) == 2
    assert all(link["title"] in ["Bulk Link 1", "Bulk Link 2"] for link in all_links)


def test_link_find(mock_database):
    # Insert a test link into the mock database
    test_link = Link(title="Findable Link", url="http://findme.com")
    test_link.save()

    # Find the link by title
    found_link = Link.find(title="Findable Link")
    assert found_link is not None
    assert found_link.title == "Findable Link"

    # Test finding a non-existent link
    missing_link = Link.find(title="Nonexistent Link")
    assert missing_link is None


def test_link_bulk_find(mock_database):
    # Insert test links into the mock database
    Link(title="Findable Link 1", url="http://findme1.com").save()
    Link(title="Findable Link 2", url="http://findme2.com").save()

    # Bulk find links
    found_links = Link.bulk_find(title={"$regex": "Findable Link.*"})
    assert len(found_links) == 2
    assert all("Findable Link" in link.title for link in found_links)


def test_link_invalid_published_at():
    # Test invalid `published_at` date
    with pytest.raises(ValidationError):
        Link(title="Invalid Date", url="http://example.com", published_at="invalid-date")


def test_link_auto_extracted_at():
    # Ensure `extracted_at` is auto-set
    link = Link(title="Auto Timestamp", url="http://example.com")
    assert link.extracted_at <= datetime.now()
    assert link.extracted_at >= datetime.now() - timedelta(seconds=5)


def test_link_save_cant_override_existing_id(mock_database):
    # Test saving a link with an existing ID
    link = Link(id=uuid4(), title="Original Link", url="http://original.com")
    link.save()

    # Save another link with the same ID
    duplicate = Link(id=link.id, title="Duplicate Link", url="http://duplicate.com")
    duplicate.save()

    # Ensure the original link was overwritten
    collection = mock_database["link"]
    found_link = collection.find_one({"_id": str(link.id)})

    assert found_link["title"] != "Duplicate Link"
    assert found_link["url"] != "http://duplicate.com"
