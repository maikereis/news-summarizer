from steps.etl.clean_links import drop_duplicated_links
from steps.etl.crawl_links import crawl_links
from zenml import pipeline


@pipeline(enable_cache=False)
def crawl(newspapers_urls: list[str]):
    step_1 = crawl_links(newspapers_urls)
    step_2 = drop_duplicated_links(after="crawl_links")
    return [step_1.invocation_id, step_2.invocation_id]
