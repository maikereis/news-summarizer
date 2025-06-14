"""Pipeline for generating training datasets."""

from steps.datasets import create_dataset, load_cleaned_articles, upload_to_huggingface
from zenml import pipeline


@pipeline
def generate_training_dataset(dataset_type: str = "preference") -> None:
    """Generate training datasets for model fine-tuning."""
    if dataset_type not in ["preference", "summarization"]:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}. Must be 'preference' or 'summarization'.")

    cleaned_articles = load_cleaned_articles(10000)
    dataset = create_dataset(cleaned_articles, dataset_type)

    repo_name = (
        "maikerdr/brazilian-news-article-summarization-DPO"
        if dataset_type == "preference"
        else "maikerdr/brazilian-news-article-summarization"
    )

    upload_to_huggingface(repo_name, dataset)
