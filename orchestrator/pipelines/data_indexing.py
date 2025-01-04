from steps.data_indexing import clean, load, store, vectorize
from zenml import pipeline


@pipeline(enable_cache=False)
def index_data():
    raw_documents = load()
    cleaned_documents = clean(raw_documents)
    embedded_documents = vectorize(cleaned_documents)

    last_step_1 = store(cleaned_documents, id="store_cleaned_docs")
    last_step_2 = store(embedded_documents, id="store_embedded_docs")

    return [last_step_1.invocation_id, last_step_2.invocation_id]
