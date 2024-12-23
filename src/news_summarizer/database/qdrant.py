import logging
from typing import Any, Dict, List, Optional

import numpy as np
from news_summarizer.config import settings
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from qdrant_client.models import PointStruct, Record

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_similarity(vector1, vector2):
    return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))


class FakeQdrantCollection:
    def __init__(self):
        self.vectors = {}

    def upsert(self, points: List[PointStruct]):
        for point in points:
            if not isinstance(point, PointStruct):
                raise ValueError("Each point must be an instance of PointStruct.")
            self.vectors[point.id] = point.model_dump()
        logger.debug("Upserted points: %s", points)

    def search(self, query_vector: List[float], limit: int, filter: Optional[Dict[str, Any]] = None):
        if not isinstance(query_vector, list) or not query_vector:
            raise ValueError("Query vector must be a non-empty list.")
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer.")

        results = [
            {
                "id": key,
                "vector": value["vector"],
                "payload": value.get("payload"),
                "similarity": calculate_similarity(query_vector, value["vector"]),
            }
            for key, value in self.vectors.items()
            if not filter or self._match_filter(value, filter)
        ]

        results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return results[:limit]

    def scroll(self, limit: int, offset: int = 0, filter: Optional[Dict[str, Any]] = None):
        points = list(self.vectors.values())

        # Apply filter if provided
        if filter:
            points = [point for point in points if self._match_filter(point, filter)]

        if offset is not None:
            offset_index = next((i for i, point in enumerate(points) if point["id"] == str(offset)), 0)
        else:
            offset_index = 0

        chunk = points[offset_index : offset_index + limit]

        chunk = [
            Record(
                id=str(point.get("id", "")),
                vector=point.get("vector"),
                payload=point.get("payload"),
            )
            for point in chunk
        ]

        next_offset = offset_index + limit if offset_index + limit < len(points) else None
        if next_offset is not None and next_offset < len(points):
            next_offset = str(points[next_offset]["id"])

        logger.debug("Scroll results: %s, next offset: %s", chunk, next_offset)
        return chunk, next_offset

    def _match_filter(self, point: Dict[str, Any], filter: Dict[str, Any]):
        for key, value in filter.items():
            if point.get("payload", {}).get(key) != value:
                return False
        return True


class FakeQdrantClient:
    def __init__(self):
        self.collections = {}

    def get_collection(self, collection_name: str):
        if collection_name not in self.collections:
            self.collections[collection_name] = FakeQdrantCollection()
        return self.collections[collection_name]

    def create_collection(self, collection_name: str, vectors_config: Optional[Dict[str, Any]] = None):
        if collection_name not in self.collections:
            self.collections[collection_name] = FakeQdrantCollection()
            logger.debug("Created collection: %s", collection_name)
        return self.collections[collection_name]

    def upsert(self, collection_name: str, points: List[PointStruct]):
        collection = self.get_collection(collection_name)
        return collection.upsert(points)

    def scroll(
        self,
        collection_name: str,
        limit: int,
        with_payload: bool = True,
        with_vectors: bool = False,
        offset: int = 0,
        filter: Optional[Dict[str, Any]] = None,
    ):
        collection = self.get_collection(collection_name)

        chunk, next_offset = collection.scroll(limit=limit, offset=offset, filter=filter)

        # Modify the results based on `with_payload` and `with_vectors` flags
        # for result in chunk:
        #    if not with_payload:
        #        result.pop("payload", True)
        #    if not with_vectors:
        #        result.pop("vector", False)

        return chunk, next_offset


class QdrantDatabaseConnector:
    _instance: QdrantClient | None = None

    def __new__(cls, *args, **kwargs) -> QdrantClient:
        if cls._instance is None:
            try:
                if settings.qdrant.use_cloud:
                    cls._instance = QdrantClient(
                        url=settings.qdrant.cloud_url,
                        api_key=settings.qdrant.apikey,
                    )

                    uri = settings.qdrant.cloud_url
                else:
                    cls._instance = QdrantClient(
                        host=settings.qdrant.host,
                        port=settings.qdrant.rest_port,
                    )

                    uri = f"{settings.qdrant.host}:{settings.qdrant.rest_port}"

                logger.info("Connection to Qdrant DB with URI successful: %s", uri)
            except UnexpectedResponse:
                logger.exception(
                    "Couldn't connect to Qdrant.",
                    host=settings.qdrant.host,
                    port=settings.qdrant.rest_port,
                    url=settings.qdrant.cloud_url,
                )

                raise

        return cls._instance


connection = QdrantDatabaseConnector()
