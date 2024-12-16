import logging

from news_summarizer.config import settings
from news_summarizer.database.mongo import MongoDatabaseConnector
from news_summarizer.domain.documents import Link
from zenml import get_step_context, step

logger = logging.getLogger(__name__)

client = MongoDatabaseConnector()
database = client.get_database(settings.mongo.name)


@step
def remove_unrelated_links():
    collection = database[Link.get_collection_name()]
    unrelated = _search_unrelated_links(collection)
    success_count, failure_count = _drop_unrelated_links(collection, unrelated)

    # Organize metadata
    metadata = {
        "total_unrelated_links": success_count + failure_count,
        "success_count": success_count,
        "failure_count": failure_count,
        "status": "success" if failure_count == 0 else "partial_success",
    }

    context = get_step_context()
    context.add_output_metadata(output_name="output", metadata=metadata)

    return metadata


def _search_unrelated_links(collection):
    filter_query = {
        "$or": [
            {"url": {"$not": {"$regex": "noticia|news|noticias", "$options": "i"}}},
            {"url": {"$not": {"$regex": ".*-.*-.*-.*-.*-.*"}}},
            {"url": {"$regex": "^.{0,99}$"}},
            {"url": {"$regex": "/video/"}},
        ]
    }

    cursor = collection.find(filter_query)
    for unrelated_group in cursor:
        yield unrelated_group


def _drop_unrelated_links(collection, unrelated):
    success_count = 0
    failure_count = 0
    try:
        for document in unrelated:
            try:
                collection.delete_one({"_id": document["_id"]})
                success_count += 1
            except Exception as exc:
                logger.error("Error trying to remove document %s: %s", document["_id"], exc)
                failure_count += 1
    except Exception as exc:
        logger.error("Error processing unrelated links: %s", exc)
        failure_count += 1
    return success_count, failure_count
