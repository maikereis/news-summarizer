import logging
import re

logger = logging.getLogger(__name__)


class FakeMongoCollection:
    def __init__(self):
        self.data = {}

    def insert_one(self, document):
        if "_id" not in document:
            raise ValueError("Document must contain an '_id' field")
        if document["_id"] in self.data:
            raise ValueError("Duplicate _id found")
        self.data[document["_id"]] = document
        logger.debug("Inserted document:", document)

    def insert_many(self, documents):
        if not documents:
            raise ValueError("Documents list cannot be empty")
        for document in documents:
            if "_id" not in document:
                raise ValueError("Each document must contain an '_id' field")
            if document["_id"] in self.data:
                raise ValueError("Duplicate _id found")
            self.data[document["_id"]] = document
        logger.debug("Inserted documents:", documents)

    def find_one(self, query):
        for document in self.data.values():
            if all(self._match_query(document, key, value) for key, value in query.items()):
                logger.debug("Found document:", document)
                return document
        logger.debug("No document found!")
        return None

    def find(self, query):
        results = [
            document
            for document in self.data.values()
            if all(self._match_query(document, key, value) for key, value in query.items())
        ]
        logger.debug("Found documents:", results)
        return results

    def _match_query(self, document, key, value):
        if isinstance(value, dict) and "$regex" in value:
            return re.search(value["$regex"], document.get(key, "")) is not None
        return document.get(key) == value


class FakeDatabase:
    def __init__(self):
        self.collections = {}

    def __getitem__(self, collection_name: str) -> FakeMongoCollection:
        # Automatically create a collection if it doesn't exist
        if collection_name not in self.collections:
            self.collections[collection_name] = FakeMongoCollection()
        return self.collections[collection_name]

    def __setitem__(self, collection_name: str, collection: FakeMongoCollection):
        self.collections[collection_name] = collection


class FakeMongoClient:
    def __init__(self):
        self.databases = {}

    def __getitem__(self, db_name: str) -> FakeDatabase:
        # Automatically create a database if it doesn't exist
        if db_name not in self.databases:
            self.databases[db_name] = FakeDatabase()
        return self.databases[db_name]

    def __setitem__(self, db_name: str, database: FakeDatabase):
        self.databases[db_name] = database


fake_connection = FakeMongoClient()
