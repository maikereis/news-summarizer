from steps.datasets import generate_datasets, load, to_hugging
from zenml import pipeline


@pipeline(enable_cache=False)
def generate(dataset_type: str = "preference") -> None:
    if dataset_type == "preference":
        cleaned_articles = load(2)
        dataset = generate_datasets(cleaned_articles, dataset_type)
        to_hugging("maikerdr/brazilian-news-article-summarization-DPO", dataset)

    elif dataset_type == "summarization":
        cleaned_articles = load(2)
        dataset = generate_datasets(cleaned_articles, dataset_type)
        to_hugging("maikerdr/brazilian-news-article-summarization", dataset)

    else:
        raise ValueError(f"Unsupported dataset_type: {dataset_type}. Must be 'preference' or 'summarization'.")
