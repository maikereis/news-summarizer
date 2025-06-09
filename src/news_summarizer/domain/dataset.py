from datasets import Dataset

from .base import VectorBaseDocument


class SummaryDatasetSample(VectorBaseDocument):
    article: str
    summary: str

    class Config:
        category = "summary_dataset_sample"


class SummaryDataset(VectorBaseDocument):
    samples: list[SummaryDatasetSample]

    def to_hfdataset(self) -> Dataset:
        data = self.model_dump()
        dataset = Dataset.from_list(data["samples"])
        return dataset

    class Config:
        category = "summary_dataset"


class PreferenceDatasetTriplet(VectorBaseDocument):
    instruction: str
    rejected: str
    chosen: str

    class Config:
        category = "preference_dataset_triplet"


class PreferenceDatasetSample(VectorBaseDocument):
    article: str
    triplets: list[PreferenceDatasetTriplet]

    class Config:
        category = "preference_dataset_sample"


class PreferenceDataset(VectorBaseDocument):
    samples: list[PreferenceDatasetSample]

    def to_hfdataset(self) -> Dataset:
        data = self.model_dump()
        dataset = Dataset.from_list(data["samples"])
        return dataset

    class Config:
        category = "preference_dataset"
