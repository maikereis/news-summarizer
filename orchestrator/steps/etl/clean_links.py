import logging

from news_summarizer.config import settings
from news_summarizer.database.mongo import MongoDatabaseConnector
from news_summarizer.domain.documents import Link
from zenml import step

logger = logging.getLogger(__name__)

client = MongoDatabaseConnector()
database = client.get_database(settings.mongo.name)


@step
def remove_unrelated_links():
    collection = database[Link.get_collection_name()]
    unrelated = _search_unrelated_links(collection)
    status = _drop_unrelated_links(collection, unrelated)
    return status


def _search_unrelated_links(collection):
    filter_query = {
        "$or": [
            {"published_at": {"$exists": False}},
            {"url": {"$not": {"$regex": "noticia|news", "$options": "i"}}},
        ]
    }
    cursor = collection.find(filter_query)
    for duplicate_group in cursor:
        yield duplicate_group


def _drop_unrelated_links(collection, unrelated):
    try:
        for document in unrelated:
            collection.delete_one({"_id": document["_id"]})
        return True
    except Exception as exc:
        logger.error("Error trying to remove unrelated links: %s", exc)
        return False
