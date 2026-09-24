"""Tokenizer abstraction for training."""

from __future__ import annotations

from dataclasses import dataclass

from training.core.errors import TrainingDependencyError


@dataclass
class TokenStats:
    count: int
    min_tokens: int
    max_tokens: int
    avg_tokens: float


class TokenizerAdapter:
    def __init__(
        self,
        *,
        model_id: str,
        max_length: int = 512,
        use_fast: bool = True,
        trust_remote_code: bool = False,
        padding_side: str = "right",
    ) -> None:
        self.model_id = model_id
        self.max_length = max_length
        self.use_fast = use_fast
        self.trust_remote_code = trust_remote_code
        self.padding_side = padding_side
        self._tokenizer = None

    def _load(self):
        if self._tokenizer is not None:
            return self._tokenizer
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise TrainingDependencyError(
                "Transformers is required for tokenization. Install training[train]."
            ) from exc
        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            use_fast=self.use_fast,
            trust_remote_code=self.trust_remote_code,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        tokenizer.padding_side = self.padding_side
        self._tokenizer = tokenizer
        return tokenizer

    @property
    def tokenizer(self):
        return self._load()

    def count_tokens(self, text: str) -> int:
        tokenizer = self._load()
        return len(tokenizer.encode(text, add_special_tokens=True))

    def compute_stats(self, texts: list[str]) -> TokenStats:
        counts = [self.count_tokens(text) for text in texts]
        return TokenStats(
            count=len(counts),
            min_tokens=min(counts),
            max_tokens=max(counts),
            avg_tokens=sum(counts) / len(counts),
        )

    def tokenize_text(self, text: str) -> dict:
        tokenizer = self._load()
        encoded = tokenizer(
            text,
            truncation=True,
            max_length=self.max_length,
            padding=False,
            return_tensors=None,
        )
        encoded["labels"] = list(encoded["input_ids"])
        return encoded
