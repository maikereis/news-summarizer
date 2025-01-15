import logging

from news_summarizer.config import settings
from news_summarizer.database.mongo import MongoDatabaseConnector
from news_summarizer.domain.documents import Link
from zenml import step

logger = logging.getLogger(__name__)

client = MongoDatabaseConnector()
database = client.get_database(settings.mongo.name)


@step
def drop_duplicated_links():
    collection = database[Link.get_collection_name()]

    duplicates = _search_duplicates(collection, group_by="url")
    status = _drop_duplicates(collection, duplicates, sort_key="extracted_at")
    return status


def _search_duplicates(collection, group_by=None):
    pipeline = [
        {"$group": {"_id": f"${group_by}", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    cursor = collection.aggregate(pipeline, allowDiskUse=True)
    for duplicate_group in cursor:
        yield duplicate_group


def _drop_duplicates(collection, duplicates_iterator, sort_key=None, descending=True):
    try:
        for duplicate in duplicates_iterator:
            ids = duplicate["ids"]

            docs = list(collection.find({"_id": {"$in": ids}}))
            if not docs:
                logger.info("No documents found for IDs: %s", ids)
                continue

            ids_to_remove = [doc["_id"] for doc in docs[1:]]

            result = collection.delete_many({"_id": {"$in": ids_to_remove}})

            logger.info("Result: %s", result)
        return True
    except Exception as exc:
        logger.error("Error trying drop duplicated articles: %s", exc)
        return False
