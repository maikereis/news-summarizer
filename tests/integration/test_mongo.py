import pytest
from news_summarizer.database.mongo import MongoDatabaseConnector


@pytest.fixture(scope="module")
def mongo_client():
    # Start the MongoDB container
    client = MongoDatabaseConnector()
    yield client
    # Cleanup after tests
    client.close()


def test_mongo_connection(mongo_client):
    # Test the connection
    assert mongo_client.admin.command("ping")["ok"] == 1.0


def test_insert_and_find(mongo_client):
    # Insert a document
    db = mongo_client.test_db
    collection = db.test_collection
    doc = {"name": "test"}
    collection.insert_one(doc)

    # Find the document
    found_doc = collection.find_one({"name": "test"})
    assert found_doc is not None
    assert found_doc["name"] == "test"
