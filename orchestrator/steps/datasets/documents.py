import logging
from typing import List, Optional

from news_summarizer.domain.clean_documents import CleanedArticle
from typing_extensions import Annotated
from zenml import get_step_context, step

logger = logging.getLogger(__name__)


@step(enable_cache=True)
def load(max_documents: Optional[int] = None) -> Annotated[List[CleanedArticle], "cleaned_documents"]:
    clean_articles = _fetch_all_cleaned_articles(max_documents=max_documents)

    metadata = {"loaded_documents": {"num_documents": len(clean_articles)}}

    context = get_step_context()
    context.add_output_metadata(output_name="cleaned_documents", metadata=metadata)

    return clean_articles


def _fetch_all_cleaned_articles(max_documents: Optional[int] = None) -> List[CleanedArticle]:
    offset = None
    documents = []

    while True:
        articles, offset = CleanedArticle.bulk_find(**{}, offset=offset)

        # Se houver limite, trunca após concatenar:
        if max_documents is not None:
            remaining = max_documents - len(documents)
            if remaining <= 0:
                break  # já bateu o limite, sai
            documents.extend(articles[:remaining])
        else:
            documents.extend(articles)

        if offset is None:
            break
        if max_documents is not None and len(documents) >= max_documents:
            break

    return documents
