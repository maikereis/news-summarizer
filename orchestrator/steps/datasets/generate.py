import logging
from typing import List, Union

from news_summarizer.datasets.generation import (
    PreferenceDatasetGenerator,
    SummarizationDatasetGenerator,
)
from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.dataset import PreferenceDataset, SummaryDataset
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)

# Define a type alias for clarity
DatasetOutput = Annotated[Union[PreferenceDataset, SummaryDataset], "generated_dataset"]


@step(enable_cache=False)
def generate_datasets(
    documents: Annotated[List[CleanedArticle], "cleaned_documents"], dataset_type: str = "preference"
) -> DatasetOutput:
    step_context = get_step_context()

    if dataset_type == "preference":
        logger.info("Start preference dataset generation")
        generator = PreferenceDatasetGenerator(cache_dir="./.model_cache")
        dataset = generator.generate(documents)

        metadata = {
            "dataset_type": "preference",
            "preference_generator": {
                "model_id": generator.model_id,
                "context_size": generator.max_input_length,
            },
        }

        step_context.add_output_metadata(metadata=metadata)
        return dataset

    elif dataset_type == "summarization":
        logger.info("Start summarization dataset generation")
        generator = SummarizationDatasetGenerator(cache_dir="./.model_cache")
        dataset = generator.generate(documents)

        metadata = {
            "dataset_type": "summarization",
            "summary_generator": {
                "model_id": generator.model_id,
                "context_size": generator.max_input_length,
            },
        }

        step_context.add_output_metadata(metadata=metadata)
        return dataset

    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}. Must be 'preference' or 'summarization'.")
