import uuid

import pytest
from news_summarizer.domain.base.nosql import NoSQLBaseLink


@pytest.fixture
def mock_database(monkeypatch):
    """
    Creates a fake database, sets up a `domain_link` collection,
    and monkeypatches the `_database` used in the tested module.
    """
    from news_summarizer.database.mongo import FakeMongoClient

    # Set up fake client and database
    fake_client = FakeMongoClient()
    _database = fake_client["test_database"]
    monkeypatch.setattr("news_summarizer.domain.base.nosql._database", _database)

    # Add sample data to `domain_link` collection
    collection = _database["domain_link"]
    collection.data.clear()
    sample_data = [
        DomainLink(id=uuid.uuid4(), name="Test Link 1", url="http://example1.com"),
        DomainLink(id=uuid.uuid4(), name="Test Link 2", url="http://example2.com"),
        DomainLink(id=uuid.uuid4(), name="Test Link 3", url="http://example3.com"),
    ]
    for link in sample_data:
        collection.insert_one(link.to_mongo())

    return _database


# Example subclass of NoSQLBaseLink for testing
class DomainLink(NoSQLBaseLink):
    name: str
    url: str

    class Settings:
        name = "domain_link"


def test_to_mongo(mock_database):
    link = DomainLink(id=uuid.uuid4(), name="Test Link", url="http://example.com")
    mongo_data = link.to_mongo()

    assert "_id" in mongo_data
    assert mongo_data["_id"] == str(link.id)
    assert mongo_data["name"] == link.name
    assert mongo_data["url"] == link.url


def test_from_mongo(mock_database):
    generated_uuid = str(uuid.uuid4())
    sample_data = {"_id": generated_uuid, "name": "Test Link ABC", "url": "http://example.com"}
    instance = DomainLink.from_mongo(sample_data)

    assert str(instance.id) == generated_uuid
    assert instance.name == sample_data["name"]
    assert instance.url == sample_data["url"]


def test_save(mock_database):
    link = DomainLink(name="Test Link XYZ", url="http://example.com")
    saved_link = link.save()

    assert saved_link is not None
    assert saved_link.name == "Test Link XYZ"

    # Verify it was added to the database
    collection = mock_database["domain_link"]
    found_link = collection.find_one({"_id": str(saved_link.id)})

    assert found_link is not None
    assert found_link["_id"] == str(link.id)
    assert found_link["name"] == "Test Link XYZ"


def test_get_or_create(mock_database):
    # Case: Object does not exist, creates it
    link = DomainLink.get_or_create(name="New Test Link", url="http://example.com")
    assert link is not None
    assert link.name == "New Test Link"

    # Case: Object exists, retrieves it
    same_link = DomainLink.get_or_create(name="New Test Link", url="http://example.com")
    assert same_link.id == link.id


def test_bulk_insert(mock_database):
    links = [
        DomainLink(name="Bulk Link 1", url="http://bulk1.com"),
        DomainLink(name="Bulk Link 2", url="http://bulk2.com"),
    ]
    success = DomainLink.bulk_insert(links)
    assert success

    # Verify the data in the database
    collection = mock_database["domain_link"]
    found_links = list(collection.data.values())

    assert len(found_links) == 5  # 3 from fixture + 2 new ones


def test_bulk_find(mock_database):
    # Test finding all links with a specific condition
    result = DomainLink.bulk_find(name="Test Link 1")
    assert len(result) == 1
    assert result[0].name == "Test Link 1"

    # Test empty result
    result = DomainLink.bulk_find(name="Nonexistent Link")
    assert result == []


def test_find(mock_database):
    # Find an existing link
    result = DomainLink.find(name="Test Link 1")
    assert result is not None
    assert result.name == "Test Link 1"

    # Test finding a non-existent link
    result = DomainLink.find(name="Nonexistent Link")
    assert result is None


def test_save_with_missing_fields(mock_database):
    # Attempt to save a link with missing required fields
    with pytest.raises(ValueError):
        DomainLink().save()


def test_find_invalid_query(mock_database):
    # Attempt to find with an invalid query structure
    assert DomainLink.find(nonexistent_field="value") is None


def test_save_cant_override_existing_id(mock_database):
    # Test saving a document with an existing ID
    link = DomainLink(id=uuid.uuid4(), name="Duplicate ID", url="http://duplicate.com")
    link.save()

    duplicate = DomainLink(id=link.id, name="Different Name", url="http://other.com")
    duplicate.save()

    collection = mock_database["domain_link"]
    found_link = collection.find_one({"_id": str(link.id)})

    # The original document should be overwritten
    assert found_link["name"] != "Different Name"
    assert found_link["url"] != "http://other.com"
