from news_summarizer.datasets.generation import SummarizationDatasetGenerator
from typing_extensions import Annotated
from zenml import get_step_context, step


@step
def get_prompts(documents: Annotated[list, "cleaned_documents"]) -> Annotated[list, "summarization_dataset"]:
    generator = SummarizationDatasetGenerator(cache_dir="./.model_cache")
    dataset = generator.generate(documents)

    metadata = {
        "summary_generator": {
            "model_id": generator.model_id,
            "context_size": generator.max_input_length,
        },
    }

    step_context = get_step_context()
    step_context.add_output_metadata(output_name="summarization_dataset", metadata=metadata)

    return dataset
