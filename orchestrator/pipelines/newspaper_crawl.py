from steps.craw_links import crawl_links
from zenml import pipeline


@pipeline(enable_cache=False)
def crawl(newspapers_urls: list[str]):
    last_step = crawl_links(newspapers_urls)
    return last_step.invocation_id
