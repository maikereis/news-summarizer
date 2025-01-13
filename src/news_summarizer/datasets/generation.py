import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from news_summarizer.config import settings
from news_summarizer.utils import RateCalculator, batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

system_prompt_template = """Você é um assistente especializado em resumir notícias
"""


summarization_prompt_template = """Resuma essa noticia. Para isso você deve: Ler toda a notícia. \
Determinar o tema central da notícia e as informações mais relevantes que o autor deseja transmitir. \
Focar nos fatos e dados mais importantes, deixando de lado detalhes secundários ou exemplos específicos. \
Evitar adicionar opiniões pessoais ou interpretações. O resumo deve refletir fielmente o conteúdo original. \
Escrever de forma direta e simples, evitando jargões ou termos técnicos desnecessários. \
Manter a ordem lógica das informações apresentadas no artigo original, garantindo que o resumo seja coeso e fácil de entender. \
Certificar-se de que todas as informações incluídas no resumo estão corretas e correspondem ao conteúdo do artigo. \

Você deve responder utilizando a mesma lingua da notícia. \
Cada resposta deve conter apenas o resumo, sem palavras chave como 'Resumo:', não deve possuir multiplos espaços entre os parágrafos.
Noticia
{article}"""


class DatasetGenerator(ABC):
    @abstractmethod
    def generate(self, **kwargs) -> None:
        raise NotImplementedError


class SummarizationDatasetGenerator(DatasetGenerator, RateCalculator):
    def __init__(
        self,
        model_id: str = settings.dataset.generator_model_id,
        device: str = settings.dataset.generator_device,
        cache_dir: Optional[Path] = None,
        task: str = "text-generation",
    ) -> None:
        self._model_id = model_id
        self._device = device

        model = AutoModelForCausalLM.from_pretrained(
            self._model_id,
            torch_dtype="auto",
            device_map=self._device,
            cache_dir=str(cache_dir) if cache_dir else None,
        )
        tokenizer = AutoTokenizer.from_pretrained(
            self._model_id,
            cache_dir=str(cache_dir) if cache_dir else None,
        )

        self.pipeline = pipeline(task, model=model, tokenizer=tokenizer)

    def create_chat_messages(self, article: str) -> List[Dict[str, str]]:
        return [
            {
                "role": "system",
                "content": system_prompt_template,
            },
            {
                "role": "user",
                "content": summarization_prompt_template.format(article=article),
            },
        ]

    def generate_responses(self, batches: List[List[Dict[str, str]]]) -> List[str]:
        responses = []
        for n_batch in batches:
            batch_summaries = self.pipeline(
                n_batch,
                max_new_tokens=512,
                return_full_text=False,
            )
            responses.extend([summary["generated_text"] for summary in batch_summaries])
        return responses

    def process_batches(self, prompts: List[Dict[str, Any]], batch_size: int = 2) -> List[Dict[str, str]]:
        articles, responses = [], []

        self._start_time = time.time()
        self._counter = 0

        for prompt_batch in batch(prompts, size=batch_size):
            # Extract articles and create chat messages
            batch_articles = [prompt.input_variables["article"] for prompt in prompt_batch]
            batch_chats = [self.create_chat_messages(prompt.content) for prompt in prompt_batch]

            # Generate responses for the chat messages
            batch_responses = self.generate_responses(batch_chats)

            # Collect results
            articles.extend(batch_articles)
            responses.extend(batch_responses)

            self._counter += batch_size
            rate = self._calculate_rate()
            logger.info("Current rate: %.2f prompts/minute", rate)

    def format_output(self, articles, responses):
        return [
            {"article": article, "summary": response} for article, response in zip(articles, responses, strict=True)
        ]

    def generate(self, prompts):
        articles, responses = self.process_batches(prompts)
        return self.format_output(articles, responses)
