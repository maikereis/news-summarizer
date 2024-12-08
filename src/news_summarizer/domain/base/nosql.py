import logging
import uuid
from abc import ABC
from typing import Dict, Generic, List, Type, TypeVar

from pydantic import UUID4, BaseModel, Field

from news_summarizer.config import settings
from news_summarizer.database.mongo import connection

logger = logging.getLogger(__name__)

_database = connection.get_database(settings.mongo.name)

T = TypeVar("T", bound="NoSQLBaseLink")


class NoSQLBaseLink(BaseModel, Generic[T], ABC):
    id: UUID4 = Field(default_factory=uuid.uuid4)

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def from_mongo(cls: Type[T], data: Dict) -> T:
        if not data:
            raise ValueError("Data is empty.")

        id = data.pop("_id")

        return cls(**dict(data, id=id))

    def to_mongo(self: T, **kwargs) -> Dict:
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
        dict_ = super().model_dump(**kwargs)

        for key, value in dict_.items():
            if isinstance(value, uuid.UUID):
                dict_[key] = str(value)

        return dict_

    def save(self: T, **kwargs) -> T | None:
        collection = _database[self.get_collection_name()]
        try:
            collection.insert_one(self.to_mongo(**kwargs))
            return self
        except Exception:
            logger.exception("Failed to insert document.")
            return None

    @classmethod
    def get_or_create(cls: Type[T], **filter_options) -> T:
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
        collection = _database[cls.get_collection_name()]
        try:
            collection.insert_many(doc.to_mongo(**kwargs) for doc in documents)

            return True
        except Exception as exc:
            logger.error("Failed to insert documents of type %s", cls.__name__, exc)
            return False

    @classmethod
    def find(cls: Type[T], **filter_options) -> T | None:
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
    def bulk_find(cls: Type[T], **filter_options) -> list[T]:
        collection = _database[cls.get_collection_name()]
        try:
            instances = collection.find(filter_options)
            return [document for instance in instances if (document := cls.from_mongo(instance)) is not None]
        except Exception:
            logger.error("Failed to retrieve documents")
            return []

    @classmethod
    def get_collection_name(cls: Type[T]) -> str:
        if not hasattr(cls, "Settings") or not hasattr(cls.Settings, "name"):
            raise NotImplementedError

        return cls.Settings.name
