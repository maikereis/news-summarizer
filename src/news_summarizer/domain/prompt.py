from news_summarizer.domain.base import VectorBaseDocument
from news_summarizer.domain.clean_documents import CleanedArticle


class Prompt(VectorBaseDocument):
    template: str
    input_variables: dict
    content: str
    num_tokens: int | None = None

    class Config:
        category = "prompt"


class GenerateDatasetSamplesPrompt(Prompt):
    data_category: str
    document: CleanedArticle
