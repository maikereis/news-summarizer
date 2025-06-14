"""Step for uploading datasets to Hugging Face Hub."""

from typing import Union

from news_summarizer.config import settings
from news_summarizer.domain.dataset import PreferenceDataset, SummaryDataset
from zenml import step


@step
def upload_to_huggingface(repository_name: str, dataset: Union[SummaryDataset, PreferenceDataset]):
    """Upload dataset to Hugging Face Hub."""
    hf_dataset = dataset.to_hfdataset()
    hf_dataset.push_to_hub(
        repository_name,
        token=settings.huggingface.access_token.get_secret_value(),
    )
