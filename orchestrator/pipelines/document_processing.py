"""Pipeline for processing and indexing documents."""

from steps.processing import clean_articles, load_articles, store_documents, vectorize_articles
from zenml import pipeline


@pipeline
def process_documents():
    """Process raw articles into clean, vectorized documents."""
    raw_articles = load_articles()
    cleaned_articles = clean_articles(raw_articles)
    embedded_chunks = vectorize_articles(cleaned_articles)

    store_documents(cleaned_articles, id="store_cleaned_articles")
    store_documents(embedded_chunks, id="store_embedded_chunks")
