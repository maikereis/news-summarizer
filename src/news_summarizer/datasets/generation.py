import json
import logging
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch
from pydantic import ValidationError
from transformers import AutoModelForCausalLM, AutoTokenizer

from news_summarizer.config import settings
from news_summarizer.domain.clean_documents import CleanedArticle
from news_summarizer.domain.dataset import (
    PreferenceDataset,
    PreferenceDatasetSample,
    PreferenceDatasetTriplet,
    SummaryDataset,
    SummaryDatasetSample,
)
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

preference_prompt_template = """Baseado na notícia abaixo extraia 3 triplas de instrução-resumo. Cada tripla deve consistir de:
1. Uma instrução pedindo para resumir a notícia de uma maneira específica.
2. Uma resposta preferida que é um trecho relevante da notícia. Contento apenas informações da notícia.
3. Uma resposta rejeitada que tenta responder a instrução com base no contexto.

Você deve responder utilizando a mesma língua da notícia. \
Sua resposta deve ter o formato JSON com a seguinte estrutura:
{{
    "triplets": [
        {{
            "instruction": "...",
            "chosen": "...",
            "rejected": "..."
        }},
        {{
            "instruction": "...",
            "chosen": "...",
            "rejected": "..."
        }},
        {{
            "instruction": "...",
            "chosen": "...",
            "rejected": "..."
        }}
    ]
}}


Notícia
{article}"""


@dataclass
class Response:
    triplets: List[PreferenceDatasetTriplet]


class DatasetGenerator(ABC):
    @abstractmethod
    def generate(self, *args, **kwargs) -> None:
        raise NotImplementedError


class SummarizationDatasetGenerator(DatasetGenerator, RateCalculator):
    """Generates summarization datasets from cleaned articles using a language model.

    This service automates the process of generating summaries for articles by interacting
    with a causal language model (LLM). It formats articles into prompt templates, sends
    them to the LLM, and parses the responses into structured dataset samples.

    Inherits:
        DatasetGenerator: Provides dataset generation interface.
        RateCalculator: Provides rate calculation utilities (prompts per minute).

    Attributes:
        _template (str): Prompt template for summarization.
        _model_id (str): Hugging Face model ID used for text generation.
        _device (str): Device identifier for model execution (e.g., 'cuda', 'cpu').
        _batch_size (int): Number of prompts processed per batch.
        _model: The loaded causal language model.
        _tokenizer: The tokenizer associated with the model.
    """

    def __init__(
        self,
        template: str = summarization_prompt_template,
        model_id: str = settings.dataset.generator_model_id,
        device: str = settings.dataset.generator_device,
        batch_size: int = 10,
        cache_dir: Optional[Path] = None,
        task: str = "text-generation",
    ) -> None:
        """Initializes the summarization dataset generator.

        Args:
            template (str): Prompt template for summarization.
            model_id (str): Hugging Face model ID for the LLM.
            device (str): Target device for model execution ('cpu', 'cuda', etc.).
            batch_size (int): Batch size for prompt processing.
            cache_dir (Optional[Path]): Directory for caching model files.
            task (str): Model task type (default is 'text-generation').
        """
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
        """str: Returns the model ID."""
        return self._model_id

    @property
    def max_input_length(self) -> int:
        """int: Maximum number of input tokens supported by the model."""
        return self._model.config.max_position_embeddings

    def _is_valid_article(self, content: str) -> bool:
        """Validates if an article content fits within the model's input limits.

        Args:
            content (str): Article content to validate.

        Returns:
            bool: True if valid (non-empty and within token limits), False otherwise.
        """
        if not content or content.strip() == "":
            logger.warning("Empty article detected and skipped.")
            return False

        prompt = self._template.format(article=content)
        num_tokens = len(self._tokenizer.encode(prompt))

        if num_tokens > self.max_input_length:
            logger.warning(
                "Article too long (%d tokens, max %d). Skipping.",
                num_tokens,
                self.max_input_length,
            )
            return False

        return True

    def _get_prompt(self, document: CleanedArticle) -> Optional[GenerateDatasetSamplesPrompt]:
        """Generates a single prompt for a document if it is valid.

        Args:
            document (CleanedArticle): The cleaned article.

        Returns:
            Optional[GenerateDatasetSamplesPrompt]: The prompt object or None if invalid.
        """
        if not self._is_valid_article(document.content):
            return None

        input_variables = {"article": document.content}
        prompt = self._template.format(**input_variables)
        num_tokens = len(self._tokenizer.encode(prompt))

        return GenerateDatasetSamplesPrompt(
            template=self._template,
            input_variables=input_variables,
            content=prompt,
            num_tokens=num_tokens,
            data_category="summarization_dataset",
            document=document,
        )

    def _get_prompts(self, documents: list[CleanedArticle]) -> list[GenerateDatasetSamplesPrompt]:
        """Generates prompts for a list of documents.

        Args:
            documents (list[CleanedArticle]): A list of cleaned articles.

        Returns:
            list[GenerateDatasetSamplesPrompt]: List of valid prompts.
        """
        prompts = []
        for doc in documents:
            prompt = self._get_prompt(doc)
            if prompt is not None:
                prompts.append(prompt)
        return prompts

    def _create_messages(self, content: str) -> List[Dict[str, str]]:
        """Formats the input content into a chat-based message structure.

        Args:
            content (str): Article content.

        Returns:
            List[Dict[str, str]]: Message structure compatible with the tokenizer's
            chat template.
        """
        return [
            {
                "role": "system",
                "content": system_prompt_template,
            },
            {
                "role": "user",
                "content": self._template.format(article=content),
            },
        ]

    def _process_batch(self, prompt_batch: List[GenerateDatasetSamplesPrompt]):
        """Processes a batch of prompts to generate summaries.

        Args:
            prompt_batch (List[GenerateDatasetSamplesPrompt]): A batch of prompts.

        Returns:
            List[str]: List of generated summary responses.
        """
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

        del model_inputs, generated_ids

        torch.cuda.empty_cache()

        return responses

    def _process_batches(self, prompts: List[GenerateDatasetSamplesPrompt]) -> List[Dict[str, str]]:
        """Processes all prompts in batches.

        Args:
            prompts (List[GenerateDatasetSamplesPrompt]): List of prompts.

        Returns:
            Tuple[List[str], List[str]]: Tuple containing article contents and
            their generated summaries.
        """
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

    def _parse_summary_sample(self, article: str, response: str) -> Optional[SummaryDatasetSample]:
        """Parses a response into a summary sample.

        Args:
            article (str): Original article content.
            response (str): Model-generated summary.

        Returns:
            Optional[SummaryDatasetSample]: Parsed dataset sample or None if parsing fails.
        """
        try:
            return SummaryDatasetSample(article=article, summary=response)
        except ValidationError as err:
            logger.error("Validation error: %s", err)
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
        return None

    def _extract_summaries(self, articles: list[str], responses: list[str]) -> list[SummaryDatasetSample]:
        """Creates summary dataset samples from articles and their responses.

        Args:
            articles (list[str]): Original articles.
            responses (list[str]): Generated summaries.

        Returns:
            list[SummaryDatasetSample]: List of valid summary samples.
        """
        samples = []
        for article, response in zip(articles, responses, strict=True):
            sample = self._parse_summary_sample(article, response)
            if sample:
                samples.append(sample)
        return samples

    def _format_output(self, articles: list[str], responses: list[str]) -> SummaryDataset:
        """Formats the articles and summaries into a dataset object.

        Args:
            articles (list[str]): Original articles.
            responses (list[str]): Generated summaries.

        Returns:
            SummaryDataset: Structured dataset with summary samples.
        """
        samples = self._extract_summaries(articles, responses)
        return SummaryDataset(samples=samples)

    def generate(self, documents: List[CleanedArticle]) -> SummaryDataset:
        """Generates a summarization dataset from a list of cleaned articles.

        Args:
            documents (List[CleanedArticle]): List of cleaned article documents.

        Returns:
            SummaryDataset: Dataset containing the article-summary pairs.

        Example:
            >>> generator = SummarizationDatasetGenerator()
            >>> dataset = generator.generate(list_of_articles)
        """
        prompts = self._get_prompts(documents)

        if not prompts:
            logger.warning("No valid prompts to process. Exiting generation.")
            return SummaryDataset(samples=[])

        articles, responses = self._process_batches(prompts)
        return self._format_output(articles, responses)


class PreferenceDatasetGenerator(DatasetGenerator, RateCalculator):
    """
    Generates preference datasets from articles using a language model.

    This generator converts articles into triplet-based representations using
    a prompt-based LLM pipeline. It performs input validation, prompt construction,
    batching, inference, and parsing of the model's output into structured data.

    Inherits:
        DatasetGenerator: Provides dataset generation interface.
        RateCalculator: Provides rate calculation utilities (prompts per minute).

    Attributes:
        template (str): Prompt template used for generation.
        model_id (str): Hugging Face model ID.
        device (str): Device for running the model (e.g., 'cuda', 'cpu').
        batch_size (int): Batch size for generation.
    """

    def __init__(
        self,
        template: str = preference_prompt_template,
        model_id: str = settings.dataset.generator_model_id,
        device: str = settings.dataset.generator_device,
        batch_size: int = 10,
        cache_dir: Optional[Path] = None,
        task: str = "text-generation",
    ) -> None:
        """
        Initialize the PreferenceDatasetGenerator.

        Args:
            template (str): Prompt template for the LLM.
            model_id (str): Hugging Face model ID.
            device (str): Device to run the model on ('cuda', 'cpu').
            batch_size (int): Number of prompts processed per batch.
            cache_dir (Optional[Path]): Local cache directory for models/tokenizers.
            task (str): Type of task, default is 'text-generation'.
        """
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
        """Returns the model ID."""
        return self._model_id

    @property
    def max_input_length(self) -> int:
        """Returns the maximum input length allowed by the model."""
        return self._model.config.max_position_embeddings

    def _is_valid_article(self, content: str) -> bool:
        """
        Checks whether the input article is valid for processing.

        Args:
            content (str): The article text.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not content or content.strip() == "":
            logger.warning("Empty article detected and skipped.")
            return False

        prompt = self._template.format(article=content)
        num_tokens = len(self._tokenizer.encode(prompt))

        if num_tokens > self.max_input_length:
            logger.warning(
                "Article too long (%d tokens, max %d). Skipping.",
                num_tokens,
                self.max_input_length,
            )
            return False

        return True

    def _get_prompt(self, document: CleanedArticle) -> Optional[GenerateDatasetSamplesPrompt]:
        """
        Constructs a prompt for a single document.

        Args:
            document (CleanedArticle): The document to generate the prompt from.

        Returns:
            GenerateDatasetSamplesPrompt | None: The generated prompt object or None if invalid.
        """
        if not self._is_valid_article(document.content):
            return None

        input_variables = {"article": document.content}
        prompt = self._template.format(**input_variables)
        num_tokens = len(self._tokenizer.encode(prompt))

        return GenerateDatasetSamplesPrompt(
            template=self._template,
            input_variables=input_variables,
            content=prompt,
            num_tokens=num_tokens,
            data_category="preference_dataset",
            document=document,
        )

    def _get_prompts(self, documents: list[CleanedArticle]) -> list[GenerateDatasetSamplesPrompt]:
        """Generates prompts for a list of documents.

        Args:
            documents (list[CleanedArticle]): A list of cleaned articles.

        Returns:
            list[GenerateDatasetSamplesPrompt]: List of valid prompts.
        """
        prompts = []
        for doc in documents:
            prompt = self._get_prompt(doc)
            if prompt is not None:
                prompts.append(prompt)
        return prompts

    def _create_messages(self, content: str) -> List[Dict[str, str]]:
        """Formats the input content into a chat-based message structure.

        Args:
            content (str): Article content.

        Returns:
            List[Dict[str, str]]: Message structure compatible with the tokenizer's
            chat template.
        """
        return [
            {
                "role": "system",
                "content": system_prompt_template,
            },
            {
                "role": "user",
                "content": self._template.format(article=content),
            },
        ]

    def _process_batch(self, prompt_batch: List[GenerateDatasetSamplesPrompt]):
        """Processes a batch of prompts to generate summaries.

        Args:
            prompt_batch (List[GenerateDatasetSamplesPrompt]): A batch of prompts.

        Returns:
            List[str]: List of generated summary responses.
        """
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

        del model_inputs, generated_ids

        torch.cuda.empty_cache()

        return responses

    def _process_batches(self, prompts: List[GenerateDatasetSamplesPrompt]) -> List[Dict[str, str]]:
        """Processes all prompts in batches.

        Args:
            prompts (List[GenerateDatasetSamplesPrompt]): List of prompts.

        Returns:
            Tuple[List[str], List[str]]: Tuple containing article contents and
            their generated summaries.
        """
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

    def _clean_markdown_block(self, triplet_str: str) -> Dict[str, Any]:
        """
        Removes markdown syntax from JSON block and parses it.

        Args:
            triplet_str (str): Markdown block with JSON content.

        Returns:
            Dict[str, Any]: Parsed JSON object.
        """
        clean_string = re.sub(r"```(?:json)?\s*|\s*```", "", triplet_str, flags=re.DOTALL).strip()
        return json.loads(clean_string)

    def _parse_preference_sample(self, article: str, response: str) -> Optional[PreferenceDatasetSample]:
        """
        Parses the response string into a PreferenceDatasetSample.

        Args:
            article (str): The input article.
            response (str): The LLM response.

        Returns:
            PreferenceDatasetSample | None: The parsed sample or None if parsing fails.
        """
        try:
            parsed = self._clean_markdown_block(response)
            sample_dict = {"article": article, "triplets": parsed["triplets"]}
            return PreferenceDatasetSample(**sample_dict)
        except (JSONDecodeError, TypeError, KeyError) as err:
            logger.error("Failed to parse triplet JSON: %s", err)
        except ValidationError as err:
            error_info = err.errors()[0]
            logger.error(
                "In '%s' list at index '%s' missing field '%s'",
                error_info["loc"][0],
                error_info["loc"][1],
                error_info["loc"][2],
            )
        except Exception as ex:
            logger.error("Unexpected error: %s", ex)
        return None

    def _extract_triplets(self, articles: List[str], responses: List[str]) -> List[PreferenceDatasetSample]:
        """
        Extracts triplet samples from article-response pairs.

        Args:
            articles (List[str]): List of articles.
            responses (List[str]): Corresponding generated responses.

        Returns:
            List[PreferenceDatasetSample]: List of valid samples.
        """
        samples = []
        for article, response in zip(articles, responses, strict=False):
            sample = self._parse_preference_sample(article, response)
            if sample:
                samples.append(sample)
        return samples

    def _format_preference_output(self, articles: List[str], responses: List[str]) -> PreferenceDataset:
        """
        Formats the articles and responses into a PreferenceDataset.

        Args:
            articles (List[str]): Articles.
            responses (List[str]): Responses.

        Returns:
            PreferenceDataset: Structured dataset object.
        """
        samples = self._extract_triplets(articles, responses)
        return PreferenceDataset(samples=samples)

    def generate(self, documents: List[CleanedArticle]) -> PreferenceDataset:
        """Generates a preference dataset from a list of cleaned articles.

        Args:
            documents (List[CleanedArticle]): List of cleaned article documents.

        Returns:
            PreferenceDataset: Generated dataset with article-preference-triplet samples.

        Example:
            >>> generator = PreferenceDatasetGenerator()
            >>> dataset = generator.generate(list_of_articles)
        """
        prompts = self._get_prompts(documents)

        if not prompts:
            logger.warning("No valid prompts to process. Exiting generation.")
            return SummaryDataset(samples=[])

        articles, responses = self._process_batches(prompts)
        return self._format_preference_output(articles, responses)
