from steps.generate_datasets import get_prompts, load
from zenml import pipeline


@pipeline(enable_cache=False)
def generate():
    cleaned_articles = load()
    last_step = get_prompts(cleaned_articles)
    return last_step.invocation_id
