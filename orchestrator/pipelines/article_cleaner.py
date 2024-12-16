from steps.etl.clean_articles import drop_duplicated_articles
from zenml import pipeline


@pipeline(enable_cache=False)
def drop_duplicates():
    last_step = drop_duplicated_articles()
    return last_step.invocation_id
