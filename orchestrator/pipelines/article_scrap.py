from steps.etl.scrap_links import scrap_links
from zenml import pipeline


@pipeline(enable_cache=False)
def scrap():
    last_step = scrap_links()
    return last_step.invocation_id
