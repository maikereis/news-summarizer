from steps.etl.clean_articles import drop_duplicated_articles
from steps.etl.scrap_articles import scrap_articles
from zenml import pipeline


@pipeline(enable_cache=False)
def scrap():
    step_1 = scrap_articles()
    step_2 = drop_duplicated_articles(after="scrap_articles")
    return [step_1.invocation_id, step_2.invocation_id]
