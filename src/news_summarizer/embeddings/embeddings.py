from functools import cached_property
from pathlib import Path
from typing import Optional

import numpy as np
from numpy.typing import NDArray
from sentence_transformers.SentenceTransformer import SentenceTransformer
from transformers import AutoTokenizer

from news_summarizer.config import settings

from .base import SingletonBase


class EmbeddingModel(SingletonBase):
    def __init__(
        self,
        model_id: str = settings.rag.embedding_model_id,
        device: str = settings.rag.model_device,
        cache_dir: Optional[Path] = None,
    ) -> None:
        self._model_id = model_id
        self._device = device

        self._model = SentenceTransformer(
            self._model_id,
            device=self._device,
            cache_folder=str(cache_dir) if cache_dir else None,
        )
        self._model.eval()

    @property
    def model_id(self) -> str:
        return self._model_id

    @cached_property
    def embedding_size(self) -> int:
        dummy_embedding = self._model.encode("", show_progress_bar=False)
        return dummy_embedding.shape[0]

    @property
    def max_input_length(self) -> int:
        return self._model.max_seq_length

    @property
    def tokenizer(self) -> AutoTokenizer:
        return self._model.tokenizer

    def __call__(
        self, input_text: str | list[str], to_list: bool = True
    ) -> NDArray[np.float32] | list[float] | list[list[float]]:
        try:
            embeddings = self._model.encode(input_text, show_progress_bar=False)
        except Exception:
            return [] if to_list else np.array([])

        if to_list:
            embeddings = embeddings.tolist()

        return embeddings
