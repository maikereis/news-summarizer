"""Step for generating training datasets."""

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


@step(enable_cache=False)
def create_dataset(
    articles: Annotated[List[CleanedArticle], "cleaned_articles"], dataset_type: str = "preference"
) -> Annotated[Union[PreferenceDataset, SummaryDataset], "generated_dataset"]:
    """Generate training dataset from cleaned articles."""
    context = get_step_context()

    if dataset_type == "preference":
        logger.info("Generating preference dataset from %d articles", len(articles))
        generator = PreferenceDatasetGenerator(cache_dir="./.model_cache")
        dataset = generator.generate(articles)

        metadata = {
            "dataset_type": "preference",
            "generator_config": {
                "model_id": generator.model_id,
                "max_input_length": generator.max_input_length,
            },
            "input_articles": len(articles),
        }

    elif dataset_type == "summarization":
        logger.info("Generating summarization dataset from %d articles", len(articles))
        generator = SummarizationDatasetGenerator(cache_dir="./.model_cache")
        dataset = generator.generate(articles)

        metadata = {
            "dataset_type": "summarization",
            "generator_config": {
                "model_id": generator.model_id,
                "max_input_length": generator.max_input_length,
            },
            "input_articles": len(articles),
        }

    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}. Must be 'preference' or 'summarization'.")

    context.add_output_metadata(output_name="generated_dataset", metadata=metadata)
    logger.info("Dataset generation completed successfully")

    return dataset
