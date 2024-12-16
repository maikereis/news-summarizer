from steps.etl.clean_links import remove_unrelated_links
from zenml import pipeline


@pipeline(enable_cache=False)
def remove_garbage():
    last_step = remove_unrelated_links()
    return last_step.invocation_id
