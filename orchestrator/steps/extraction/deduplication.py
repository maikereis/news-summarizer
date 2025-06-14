"""Steps for removing duplicate links and articles."""

import logging

from news_summarizer.config import settings
from news_summarizer.database.mongo import MongoDatabaseConnector
from news_summarizer.domain.documents import Article, Link
from zenml import step

logger = logging.getLogger(__name__)

client = MongoDatabaseConnector()
database = client.get_database(settings.mongo.name)


@step
def remove_duplicate_links():
    """Remove duplicate links from the database."""
    collection = database[Link.get_collection_name()]
    duplicates = _find_duplicates(collection, group_by="url")
    return _remove_duplicates(collection, duplicates)


@step
def remove_duplicate_articles():
    """Remove duplicate articles from the database."""
    collection = database[Article.get_collection_name()]
    duplicates = _find_duplicates(collection, group_by="url")
    return _remove_duplicates(collection, duplicates)


def _find_duplicates(collection, group_by: str):
    """Find duplicate documents in collection."""
    pipeline = [
        {"$group": {"_id": f"${group_by}", "count": {"$sum": 1}, "ids": {"$push": "$_id"}}},
        {"$match": {"count": {"$gt": 1}}},
    ]
    return collection.aggregate(pipeline, allowDiskUse=True)


def _remove_duplicates(collection, duplicates_cursor) -> bool:
    """Remove duplicate documents, keeping the first occurrence."""
    try:
        total_removed = 0
        for duplicate_group in duplicates_cursor:
            ids = duplicate_group["ids"]

            # Keep first document, remove the rest
            ids_to_remove = ids[1:]
            if ids_to_remove:
                result = collection.delete_many({"_id": {"$in": ids_to_remove}})
                total_removed += result.deleted_count

        logger.info("Removed %d duplicate documents", total_removed)
        return True

    except Exception as exc:
        logger.error("Failed to remove duplicates: %s", exc)
        return False
