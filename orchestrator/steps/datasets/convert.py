from typing import Union

from news_summarizer.config import settings
from news_summarizer.domain.dataset import PreferenceDataset, SummaryDataset
from zenml import step


@step(enable_cache=True)
def to_hugging(name: str, dataset: Union[SummaryDataset, PreferenceDataset]):
    hf_dataset = dataset.to_hfdataset()
    hf_dataset.push_to_hub(
        name,
        token=settings.huggingface.access_token.get_secret_value(),
    )
