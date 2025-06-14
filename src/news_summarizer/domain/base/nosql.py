import logging
import uuid
from abc import ABC
from typing import Dict, Generic, List, Type, TypeVar

from pydantic import UUID4, BaseModel, Field

from news_summarizer.config import settings
from news_summarizer.database.mongo import connection

logger = logging.getLogger(__name__)

_database = connection.get_database(settings.mongo.name)

T = TypeVar("T", bound="NoSQLBaseDocument")


class NoSQLBaseDocument(BaseModel, Generic[T], ABC):
    """
    Abstract base class for MongoDB-backed NoSQL documents.

    This class provides a bridge between Pydantic models and MongoDB collections,
    allowing seamless serialization, deserialization, and database operations
    such as insertion, querying, and bulk operations.

    The class uses the Active Record pattern, enabling document instances to
    perform database operations on themselves and their collections.

    Attributes:
        id (UUID4): Unique identifier for the document, auto-generated if not provided.

    Example:
        Define a concrete document class:

        >>> class NewsArticle(NoSQLBaseDocument['NewsArticle']):
        ...     title: str
        ...     content: str
        ...
        ...     class Config:
        ...         name = "news_articles"
        ...
        >>> article = NewsArticle(title="AI Breakthrough", content="New developments in AI...")
        >>> article.save()
        <NewsArticle id=...>

        Retrieve documents:

        >>> found_article = NewsArticle.find(title="AI Breakthrough")
        >>> print(found_article.content)
        New developments in AI...

        Bulk insert documents:

        >>> articles = [
        ...     NewsArticle(title="Title 1", content="Content 1"),
        ...     NewsArticle(title="Title 2", content="Content 2"),
        ... ]
        >>> NewsArticle.bulk_insert(articles)
        True

        Bulk find documents:

        >>> results = NewsArticle.bulk_find()
        >>> for doc in results:
        ...     print(doc.title)

        Get or create a document:

        >>> doc = NewsArticle.get_or_create(title="Unique Title")
        >>> print(doc.id)
    """

    id: UUID4 = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        """
        Compare documents by their unique ID.

        Args:
            value (object): Object to compare with.

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
        """
        Generate hash based on document ID for use in sets and dicts.

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
    def from_mongo(cls: Type[T], data: Dict) -> T:
        """
        Create document instance from MongoDB document dictionary.

        Converts MongoDB document format (with '_id') into Pydantic model,
        mapping '_id' to 'id'.

        Args:
            data (Dict): MongoDB document data.

        Returns:
            T: Document instance of the calling class.

        Raises:
            ValueError: If the input data is empty.

        Example:
            >>> mongo_data = {"_id": uuid.uuid4(), "title": "Test"}
            >>> article = NewsArticle.from_mongo(mongo_data)
            >>> print(article.title)
            Test
        """
        if not data:
            raise ValueError("Data is empty.")

        id = data.pop("_id")
        return cls(**dict(data, id=id))

    def to_mongo(self: T, **kwargs) -> Dict:
        """
        Convert document instance to dictionary suitable for MongoDB insertion.

        Serializes the Pydantic model, converts UUID to string, and
        renames 'id' field to '_id' for MongoDB.

        Args:
            **kwargs: Arguments passed to model_dump.

        Returns:
            Dict: Serialized document dictionary for MongoDB.

        Example:
            >>> article = NewsArticle(title="Test")
            >>> mongo_dict = article.to_mongo()
            >>> "_id" in mongo_dict
            True
        """
        exclude_unset = kwargs.pop("exclude_unset", False)
        by_alias = kwargs.pop("by_alias", True)

        parsed = self.model_dump(exclude_unset=exclude_unset, by_alias=by_alias, **kwargs)

        if "_id" not in parsed and "id" in parsed:
            parsed["_id"] = str(parsed.pop("id"))

        for key, value in parsed.items():
            if isinstance(value, uuid.UUID):
                parsed[key] = str(value)
        logger.debug("Inserting: %s", parsed)
        return parsed

    def model_dump(self: T, **kwargs) -> Dict:
        """
        Serialize document to dictionary with UUIDs converted to strings.

        Extends Pydantic's model_dump to ensure UUID compatibility with MongoDB.

        Args:
            **kwargs: Arguments passed to parent model_dump().

        Returns:
            Dict: Serialized document dictionary.

        Example:
            >>> article = NewsArticle(title="Test")
            >>> data = article.model_dump()
            >>> isinstance(data['id'], str)
            True
        """
        dict_ = super().model_dump(**kwargs)
        for key, value in dict_.items():
            if isinstance(value, uuid.UUID):
                dict_[key] = str(value)
        return dict_

    def save(self: T, **kwargs) -> T | None:
        """
        Insert the document into its MongoDB collection.

        Returns the instance on success, or None on failure.

        Args:
            **kwargs: Arguments passed to to_mongo().

        Returns:
            T | None: The saved document instance or None if insertion failed.

        Example:
            >>> article = NewsArticle(title="Test")
            >>> saved_article = article.save()
            >>> saved_article is not None
            True
        """
        collection = _database[self.get_collection_name()]
        try:
            collection.insert_one(self.to_mongo(**kwargs))
            return self
        except Exception:
            logger.exception("Failed to insert document.")
            return None

    @classmethod
    def get_or_create(cls: Type[T], **filter_options) -> T:
        """
        Retrieve a document matching filter options or create it if not found.

        Args:
            **filter_options: Filter criteria to find or create the document.

        Returns:
            T: Retrieved or newly created document.

        Raises:
            Exception: Propagates exceptions if retrieval or creation fails.

        Example:
            >>> doc = NewsArticle.get_or_create(title="Unique Title")
            >>> print(doc.id)
        """
        collection = _database[cls.get_collection_name()]
        try:
            instance = collection.find_one(filter_options)
            if instance:
                return cls.from_mongo(instance)

            new_instance = cls(**filter_options)
            new_instance = new_instance.save()
            return new_instance
        except Exception:
            logger.exception("Failed to retrieve document with filter options: %s", filter_options)
            raise

    @classmethod
    def bulk_insert(cls: Type[T], documents: List[T], **kwargs) -> bool:
        """
        Insert multiple documents into the collection.

        Args:
            documents (List[T]): List of document instances to insert.
            **kwargs: Arguments passed to to_mongo() for each document.

        Returns:
            bool: True if insertion succeeded, False otherwise.

        Example:
            >>> docs = [NewsArticle(title="1"), NewsArticle(title="2")]
            >>> success = NewsArticle.bulk_insert(docs)
            >>> success
            True
        """
        collection = _database[cls.get_collection_name()]
        try:
            collection.insert_many(doc.to_mongo(**kwargs) for doc in documents)
            return True
        except Exception as exc:
            logger.error("Failed to insert documents of type %s", cls.__name__, exc)
            return False

    @classmethod
    def find(cls: Type[T], **filter_options) -> T | None:
        """
        Find a single document matching the given filter criteria.

        Args:
            **filter_options: Filter criteria.

        Returns:
            T | None: Document instance if found, else None.

        Example:
            >>> article = NewsArticle.find(title="Test")
            >>> if article:
            ...     print(article.title)
        """
        collection = _database[cls.get_collection_name()]
        try:
            instance = collection.find_one(filter_options)
            if instance:
                return cls.from_mongo(instance)
            return None
        except Exception as e:
            logger.error("Failed to retrieve document: %s", e)
            return None

    @classmethod
    def bulk_find(cls: Type[T], **filter_options) -> List[T]:
        """
        Find multiple documents matching the filter criteria.

        Args:
            **filter_options: Filter criteria.

        Returns:
            List[T]: List of found document instances.

        Example:
            >>> articles = NewsArticle.bulk_find(title={"$regex": "AI"})
            >>> for article in articles:
            ...     print(article.title)
        """
        collection = _database[cls.get_collection_name()]
        try:
            instances = collection.find(filter_options)
            return [doc for instance in instances if (doc := cls.from_mongo(instance)) is not None]
        except Exception:
            logger.error("Failed to retrieve documents")
            return []

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        """
        Return the MongoDB collection name defined in the nested Config class.

        Raises:
            NotImplementedError: If Config.name is not defined in the subclass.

        Returns:
            str: Collection name.

        Example:
            >>> NewsArticle.get_collection_name()
            'news_articles'
        """
        if not hasattr(cls, "Config") or not hasattr(cls.Config, "name"):
            raise NotImplementedError("Subclasses must define a nested Config class with a 'name' attribute.")
        return cls.Config.name
