import logging
import uuid
from abc import ABC
from typing import Any, Callable, Dict, Generic, Type, TypeVar
from uuid import UUID

import numpy as np
from pydantic import UUID4, BaseModel, Field
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import CollectionInfo, PointStruct, Record

from news_summarizer.database.qdrant import connection
from news_summarizer.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)

T = TypeVar("T", bound="VectorBaseDocument")


class VectorBaseDocument(BaseModel, Generic[T], ABC):
    """Abstract base class for vector-enabled documents in Qdrant database.

    This class provides an Object-Vector Mapping (OVM) layer that bridges
    Pydantic models with Qdrant vector database operations. It handles document
    serialization, vector operations, and collection management.

    The class uses the Active Record pattern, allowing documents to perform
    database operations on themselves and their collections.

    Attributes:
        id (UUID4): Unique identifier for the document, auto-generated if not provided.

    Example:
        Define a concrete document class:

        >>> class NewsArticle(VectorBaseDocument['NewsArticle']):
        ...     title: str
        ...     content: str
        ...     embedding: Optional[List[float]] = None
        ...
        ...     class Config:
        ...         name = "news_articles"
        ...         category = "news"
        ...         use_vector_index = True

        Create and insert documents:

        >>> article = NewsArticle(
        ...     title="AI Breakthrough",
        ...     content="New developments in artificial intelligence...",
        ...     embedding=[0.1, 0.2, 0.3, ...]  # 768-dim vector
        ... )
        >>> NewsArticle.bulk_insert([article])
        True

        Search for similar documents:

        >>> query_vector = [0.15, 0.25, 0.35, ...]
        >>> similar_articles = NewsArticle.search(query_vector, limit=5)
        >>> for article in similar_articles:
        ...     print(f"Found: {article.title}")
    """

    id: UUID4 = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        """Compare documents by their unique ID.

        Args:
            value: Object to compare with.

        Returns:
            bool: True if both documents have the same ID and class.

        Example:
            >>> doc1 = NewsArticle(title="Test")
            >>> doc2 = NewsArticle(id=doc1.id, title="Different Title")
            >>> doc1 == doc2
            True
        """
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        """Generate hash based on document ID for use in sets and dicts.

        Returns:
            int: Hash value of the document ID.

        Example:
            >>> doc = NewsArticle(title="Test")
            >>> doc_set = {doc}
            >>> len(doc_set)
            1
        """
        return hash(self.id)

    @classmethod
    def from_record(cls: Type[T], point: Record) -> T:
        """Create document instance from Qdrant Record.

        Reconstructs a document object from data retrieved from Qdrant,
        handling ID conversion and optional embedding vectors.

        Args:
            point (Record): Qdrant record containing document data.

        Returns:
            T: Document instance of the calling class.

        Example:
            >>> # Assuming 'record' is a Record from Qdrant search results
            >>> article = NewsArticle.from_record(record)
            >>> print(f"Restored article: {article.title}")
        """
        _id = UUID(point.id, version=4)
        payload = point.payload or {}

        attributes = {
            "id": _id,
            **payload,
        }
        if cls._has_class_attribute("embedding"):
            attributes["embedding"] = point.vector or None

        return cls(**attributes)

    def to_point(self: T, **kwargs) -> PointStruct:
        """Convert document to Qdrant PointStruct for database operations.

        Serializes the document into a format suitable for Qdrant storage,
        separating metadata from vector data and handling numpy arrays.

        Args:
            **kwargs: Additional arguments passed to model_dump().
                exclude_unset (bool): Exclude unset fields. Defaults to False.
                by_alias (bool): Use field aliases. Defaults to True.

        Returns:
            PointStruct: Qdrant point structure ready for insertion.

        Example:
            >>> article = NewsArticle(title="Test", embedding=[0.1, 0.2])
            >>> point = article.to_point()
            >>> print(f"Point ID: {point.id}")
            >>> print(f"Vector length: {len(point.vector)}")
        """
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        payload = self.model_dump(exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

        _id = str(payload.pop("id"))
        vector = payload.pop("embedding", {})
        if vector and isinstance(vector, np.ndarray):
            vector = vector.tolist()

        return PointStruct(id=_id, vector=vector, payload=payload)

    def model_dump(self: T, **kwargs) -> dict:
        """Serialize document to dictionary with UUID string conversion.

        Extends Pydantic's model_dump to handle UUID serialization for
        Qdrant compatibility.

        Args:
            **kwargs: Arguments passed to parent model_dump().

        Returns:
            dict: Serialized document data with UUIDs as strings.

        Example:
            >>> article = NewsArticle(title="Test")
            >>> data = article.model_dump()
            >>> isinstance(data['id'], str)
            True
        """
        dict_ = super().model_dump(**kwargs)
        dict_ = self._uuid_to_str(dict_)
        return dict_

    def _uuid_to_str(self, item: Any) -> Any:
        """Recursively convert UUID objects to strings in nested structures.

        Args:
            item: Data structure potentially containing UUIDs.

        Returns:
            Any: Data structure with UUIDs converted to strings.
        """
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, UUID):
                    item[key] = str(value)
                elif isinstance(value, list):
                    item[key] = [self._uuid_to_str(v) for v in value]
                elif isinstance(value, dict):
                    item[key] = {k: self._uuid_to_str(v) for k, v in value.items()}

        return item

    @classmethod
    def bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> bool:
        """Insert multiple documents into the collection with error handling.

        Creates the collection if it doesn't exist, then performs bulk insertion
        of documents. This is the preferred method for inserting multiple documents.

        Args:
            documents (list[VectorBaseDocument]): Documents to insert.

        Returns:
            bool: True if insertion succeeded, False otherwise.

        Example:
            >>> articles = [
            ...     NewsArticle(title="Article 1", content="Content 1"),
            ...     NewsArticle(title="Article 2", content="Content 2")
            ... ]
            >>> success = NewsArticle.bulk_insert(articles)
            >>> if success:
            ...     print("Articles inserted successfully")
        """
        try:
            cls.get_or_create_collection()
        except Exception as exc:
            logger.error("Neither the collection exists or can be created: %s.", exc)
            return False

        try:
            cls._bulk_insert(documents)
        except Exception as exc:
            logger.error("Error trying to insert documents: %s.", exc)
            return False
        return True

    @classmethod
    def _bulk_insert(cls: Type[T], documents: list["VectorBaseDocument"]) -> None:
        """Internal method to perform the actual bulk insertion.

        Args:
            documents (list[VectorBaseDocument]): Documents to insert.

        Raises:
            Exception: If Qdrant insertion fails.
        """
        points = [doc.to_point() for doc in documents]
        connection.upsert(collection_name=cls.get_collection_name(), points=points)

    @classmethod
    def bulk_find(cls: Type[T], limit: int = 10, **kwargs) -> tuple[list[T], UUID | None]:
        """Retrieve documents with pagination support and error handling.

        Performs a scroll operation to retrieve documents from the collection
        with optional filtering and pagination.

        Args:
            limit (int): Maximum number of documents to retrieve. Defaults to 10.
            **kwargs: Additional arguments for scroll operation.
                offset (UUID | None): Starting point for pagination.
                with_payload (bool): Include document payload. Defaults to True.
                with_vectors (bool): Include vector data. Defaults to False.
                scroll_filter (dict): Optional scroll filter for querying specific fields.

        Returns:
            tuple[list[T], UUID | None]: Documents and next pagination offset.

        Example:
            >>> # Get first batch of articles
            >>> articles, next_offset = NewsArticle.bulk_find(limit=5)
            >>> print(f"Found {len(articles)} articles")
            >>>
            >>> # Get next batch using offset
            >>> if next_offset:
            ...     more_articles, _ = NewsArticle.bulk_find(limit=5, offset=next_offset)
            >>>
            >>> # Find articles with specific title
            >>> title = "Veja o que é #FATO ou #FAKE em vídeos que viralizaram durante o conflito entre Israel e Hamas"
            >>> filter_ = {
            ...     "must": [
            ...         {
            ...             "key": "title",
            ...             "match": {"value": title}
            ...         }
            ...     ]
            ... }
            >>> articles, _ = NewsArticle.bulk_find(limit=2, scroll_filter=filter_)
            >>> print(f"Filtered results: {len(articles)} found")
        """
        try:
            documents, next_offset = cls._bulk_find(limit=limit, **kwargs)
        except Exception:
            documents, next_offset = [], None

        return documents, next_offset

    @classmethod
    def _bulk_find(cls: Type[T], limit: int = 10, **kwargs) -> tuple[list[T], UUID | None]:
        """Internal method to perform the actual bulk find operation.

        Args:
            limit (int): Maximum number of documents to retrieve.
            **kwargs: Additional arguments for scroll operation.

        Returns:
            tuple[list[T], UUID | None]: Documents and next pagination offset.
        """
        collection_name = cls.get_collection_name()

        offset = kwargs.pop("offset", None)
        offset = str(offset) if offset else None

        records, next_offset = connection.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            offset=offset,
            **kwargs,
        )

        documents = [cls.from_record(record) for record in records]

        if next_offset is not None:
            next_offset = UUID(next_offset, version=4)

        return documents, next_offset

    @classmethod
    def search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        """Perform vector similarity search with error handling.

        Searches for documents similar to the provided query vector using
        cosine similarity (or configured distance metric).

        Args:
            query_vector (list): Query vector for similarity search.
            limit (int): Maximum number of results to return. Defaults to 10.
            **kwargs: Additional arguments for search operation.
                with_payload (bool): Include document payload. Defaults to True.
                with_vectors (bool): Include vector data. Defaults to False.
                filter: Optional filter conditions.

        Returns:
            list[T]: Documents ordered by similarity score (most similar first).

        Example:
            >>> # Search for articles similar to a query
            >>> embedding_model = EmbeddingModel()
            >>> query_vector = embedding_model.encode("artificial intelligence news")
            >>> similar_articles = NewsArticle.search(
            ...     query_vector=query_vector,
            ...     limit=3
            ... )
            >>> for article in similar_articles:
            ...     print(f"Similar: {article.title}")
        """
        try:
            documents = cls._search(query_vector=query_vector, limit=limit, **kwargs)
        except Exception:
            logger.error("Failed to search documents in: %s", cls.get_collection_name())
            documents = []

        return documents

    @classmethod
    def _search(cls: Type[T], query_vector: list, limit: int = 10, **kwargs) -> list[T]:
        """Internal method to perform the actual vector search.

        Args:
            query_vector (list): Query vector for similarity search.
            limit (int): Maximum number of results to return.
            **kwargs: Additional arguments for search operation.

        Returns:
            list[T]: Documents ordered by similarity score.
        """
        collection_name = cls.get_collection_name()
        records = connection.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            with_payload=kwargs.pop("with_payload", True),
            with_vectors=kwargs.pop("with_vectors", False),
            **kwargs,
        )

        documents = [cls.from_record(record) for record in records]

        return documents

    @classmethod
    def get_or_create_collection(cls: Type[T]) -> CollectionInfo:
        """Get existing collection or create it if it doesn't exist.

        This method ensures the collection exists before performing operations.
        It configures vector indexing based on the class configuration.

        Returns:
            CollectionInfo: Information about the collection.

        Raises:
            RuntimeError: If collection creation fails.

        Example:
            >>> # Ensure collection exists before bulk operations
            >>> collection_info = NewsArticle.get_or_create_collection()
            >>> print(f"Collection: {collection_info.name}")
            >>> print(f"Vector count: {collection_info.vectors_count}")
        """
        collection_name = cls.get_collection_name()

        try:
            return connection.get_collection(collection_name=collection_name)
        except Exception:
            use_vector_index = cls.get_use_vector_index()

            collection_created = cls._create_collection(
                collection_name=collection_name, use_vector_index=use_vector_index
            )

            if collection_created is False:
                raise RuntimeError(f"Couldn't create collection {collection_name}") from None

            return connection.get_collection(collection_name=collection_name)

    @classmethod
    def create_collection(cls: Type[T]) -> bool:
        """Create a new collection for this document type.

        Returns:
            bool: True if collection was created successfully.

        Example:
            >>> success = NewsArticle.create_collection()
            >>> if success:
            ...     print("Collection created")
        """
        collection_name = cls.get_collection_name()
        use_vector_index = cls.get_use_vector_index()

        return cls._create_collection(collection_name=collection_name, use_vector_index=use_vector_index)

    @classmethod
    def _create_collection(cls, collection_name: str, use_vector_index: bool = True) -> bool:
        """Internal method to create a collection with vector configuration.

        Args:
            collection_name (str): Name of the collection to create.
            use_vector_index (bool): Whether to configure vector indexing.

        Returns:
            bool: True if collection was created successfully.
        """
        if use_vector_index is True:
            vectors_config = VectorParams(size=EmbeddingModel().embedding_size, distance=Distance.COSINE)
        else:
            vectors_config = {}

        return connection.create_collection(collection_name=collection_name, vectors_config=vectors_config)

    @classmethod
    def get_category(cls: Type[T]) -> object:
        """Get the data category for this document type.

        Returns:
            object: Category value from class configuration.

        Raises:
            Exception: If category is not configured in Config class.

        Example:
            >>> category = NewsArticle.get_category()
            >>> print(f"Document category: {category}")
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "category"):
            raise Exception(
                "The class should define a Config class with"
                "the 'category' property that reflects the collection's data category."
            )

        return cls.Config.category

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        """Get the Qdrant collection name for this document type.

        Returns:
            str: Collection name from class configuration.

        Raises:
            Exception: If collection name is not configured in Config class.

        Example:
            >>> name = NewsArticle.get_collection_name()
            >>> print(f"Collection name: {name}")
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "name"):
            raise Exception(
                "The class should define a Config class with" "the 'name' property that reflects the collection's name."
            )

        return cls.Config.name

    @classmethod
    def get_use_vector_index(cls: Type[T]) -> bool:
        """Check if this document type uses vector indexing.

        Returns:
            bool: True if vector indexing is enabled, defaults to True.

        Example:
            >>> uses_vectors = NewsArticle.get_use_vector_index()
            >>> print(f"Uses vector indexing: {uses_vectors}")
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "use_vector_index"):
            return True

        return cls.Config.use_vector_index

    @classmethod
    def group_by_class(
        cls: Type["VectorBaseDocument"], documents: list["VectorBaseDocument"]
    ) -> Dict["VectorBaseDocument", list["VectorBaseDocument"]]:
        """Group documents by their class type.

        Useful for processing mixed collections of different document types.

        Args:
            documents (list[VectorBaseDocument]): Documents to group.

        Returns:
            Dict[VectorBaseDocument, list[VectorBaseDocument]]: Documents grouped by class.

        Example:
            >>> mixed_docs = [news_article, blog_post, research_paper]
            >>> grouped = VectorBaseDocument.group_by_class(mixed_docs)
            >>> for doc_class, docs in grouped.items():
            ...     print(f"{doc_class.__name__}: {len(docs)} documents")
        """
        return cls._group_by(documents, selector=lambda doc: doc.__class__)

    @classmethod
    def group_by_category(cls: Type[T], documents: list[T]) -> Dict[object, list[T]]:
        """Group documents by their configured category.

        Args:
            documents (list[T]): Documents to group.

        Returns:
            Dict[object, list[T]]: Documents grouped by category.

        Example:
            >>> articles = NewsArticle.bulk_find(limit=100)[0]
            >>> grouped = NewsArticle.group_by_category(articles)
            >>> for category, docs in grouped.items():
            ...     print(f"Category {category}: {len(docs)} documents")
        """
        return cls._group_by(documents, selector=lambda doc: doc.get_category())

    @classmethod
    def _group_by(cls: Type[T], documents: list[T], selector: Callable[[T], Any]) -> Dict[object, list[T]]:
        """Internal method to group documents by a selector function.

        Args:
            documents (list[T]): Documents to group.
            selector (Callable[[T], Any]): Function to determine grouping key.

        Returns:
            Dict[object, list[T]]: Grouped documents.
        """
        grouped = {}
        for doc in documents:
            key = selector(doc)

            if key not in grouped:
                grouped[key] = []

            grouped[key].append(doc)

        return grouped

    @classmethod
    def collection_name_to_class(cls: Type["VectorBaseDocument"], collection_name: str) -> type["VectorBaseDocument"]:
        """Find the document class that corresponds to a collection name.

        Recursively searches through all subclasses to find the one
        configured for the specified collection name.

        Args:
            collection_name (str): Name of the collection to find class for.

        Returns:
            type[VectorBaseDocument]: Document class for the collection.

        Raises:
            ValueError: If no class is found for the collection name.

        Example:
            >>> doc_class = VectorBaseDocument.collection_name_to_class("news_articles")
            >>> print(f"Found class: {doc_class.__name__}")
            >>> # Create instance of found class
            >>> instance = doc_class(title="Dynamic Creation")
        """
        for subclass in cls.__subclasses__():
            try:
                if subclass.get_collection_name() == collection_name:
                    return subclass
            except Exception:
                pass

            try:
                return subclass.collection_name_to_class(collection_name)
            except ValueError:
                continue

        raise ValueError(f"No subclass found for collection name: {collection_name}")

    @classmethod
    def _has_class_attribute(cls: Type[T], attribute_name: str) -> bool:
        """Check if the class or its bases have a specific attribute.

        Used internally to determine if a class has certain fields like 'embedding'.

        Args:
            attribute_name (str): Name of the attribute to check.

        Returns:
            bool: True if the attribute exists in the class hierarchy.
        """
        if attribute_name in cls.__annotations__:
            return True

        for base in cls.__bases__:
            if hasattr(base, "_has_class_attribute") and base._has_class_attribute(attribute_name):
                return True

        return False
