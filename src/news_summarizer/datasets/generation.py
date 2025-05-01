import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from news_summarizer.config import settings
from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.prompt import GenerateDatasetSamplesPrompt
from news_summarizer.utils import RateCalculator, batch

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

system_prompt_template = """Você é um assistente especializado em resumir notícias
"""


summarization_prompt_template = """Resuma essa notícia. Para isso você deve: Ler toda a notícia. \
Determinar o tema central da notícia e as informações mais relevantes que o autor deseja transmitir. \
Focar nos fatos e dados mais importantes, deixando de lado detalhes secundários ou exemplos específicos. \
Evitar adicionar opiniões pessoais ou interpretações. O resumo deve refletir fielmente o conteúdo original. \
Escrever de forma direta e simples, evitando jargões ou termos técnicos desnecessários. \
Manter a ordem lógica das informações apresentadas no artigo original, garantindo que o resumo seja coeso e fácil de entender. \
Certificar-se de que todas as informações incluídas no resumo estão corretas e correspondem ao conteúdo do artigo. \

Você deve responder utilizando a mesma língua da notícia. \
Cada resposta deve conter apenas o resumo, sem palavras-chave como 'Resumo:', não deve possuir múltiplos espaços entre os parágrafos.
Notícia
{article}"""


class DatasetGenerator(ABC):
    @abstractmethod
    def generate(self, **kwargs) -> None:
        raise NotImplementedError


class SummarizationDatasetGenerator(DatasetGenerator, RateCalculator):
    def __init__(
        self,
        template: str = summarization_prompt_template,
        model_id: str = settings.dataset.generator_model_id,
        device: str = settings.dataset.generator_device,
        batch_size: int = 10,
        cache_dir: Optional[Path] = None,
        task: str = "text-generation",
    ) -> None:
        self._template = template
        self._model_id = model_id
        self._device = device

        self._model = AutoModelForCausalLM.from_pretrained(
            self._model_id,
            torch_dtype=torch.float16,
            device_map=self._device,
            max_memory={0: "8GB"},
            cache_dir=str(cache_dir) if cache_dir else None,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(
            self._model_id,
            cache_dir=str(cache_dir) if cache_dir else None,
            padding_side="left",
        )

        self._batch_size = batch_size

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def max_input_length(self) -> int:
        return self._model.config.max_position_embeddings

    def _get_prompt(self, document: CleanedArticle) -> GenerateDatasetSamplesPrompt:
        input_variables = {"article": document.content}
        prompt = self._template.format(**input_variables)
        prompt_tokens = self._tokenizer.encode(prompt)
        num_tokens = len(prompt_tokens)

        generated_dataset_sample = GenerateDatasetSamplesPrompt(
            template=summarization_prompt_template,
            input_variables=input_variables,
            content=prompt,
            num_tokens=num_tokens,
            data_category="summariation_dataset",
            document=document,
        )

        return generated_dataset_sample

    def _get_prompts(self, documents: list[CleanedArticle]) -> list[GenerateDatasetSamplesPrompt]:
        return [self._get_prompt(document) for document in documents]

    def _create_messages(self, article: str) -> List[Dict[str, str]]:
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

    def _process_batch(self, prompt_batch: List[GenerateDatasetSamplesPrompt]):
        # Create messages for all prompts in the batch
        messages_batch = [self._create_messages(prompt.content) for prompt in prompt_batch]

        # Apply chat template and tokenize in batch
        texts = [
            self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            for messages in messages_batch
        ]
        model_inputs = self._tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self._model.device)

        with torch.no_grad():
            # Generate responses in batch
            generated_ids = self._model.generate(**model_inputs, max_new_tokens=512)

        input_lengths = [len(input_ids) for input_ids in model_inputs.input_ids]

        # Decode responses and remove input tokens
        responses = [
            self._tokenizer.decode(output_ids[input_length:], skip_special_tokens=True)
            for output_ids, input_length in zip(generated_ids, input_lengths, strict=False)
        ]

        torch.cuda.empty_cache()

        return responses

    def _process_batches(self, prompts: List[GenerateDatasetSamplesPrompt]) -> List[Dict[str, str]]:
        articles, responses = [], []

        self._start_time = time.time()
        self._counter = 0

        for prompt_batch in batch(prompts, size=self._batch_size):
            batch_articles = [prompt.input_variables["article"] for prompt in prompt_batch]
            batch_responses = self._process_batch(prompt_batch)

            articles.extend(batch_articles)
            responses.extend(batch_responses)

            self._counter += self._batch_size
            rate = self._calculate_rate()
            logger.info("Current rate: %.2f prompts/minute", rate)
        return articles, responses

    def _format_output(self, articles, responses):
        return [
            {"article": article, "summary": response} for article, response in zip(articles, responses, strict=True)
        ]

    def generate(self, documents: List[CleanedArticle]):
        prompts = self._get_prompts(documents)
        articles, responses = self._process_batches(prompts)
        return self._format_output(articles, responses)
