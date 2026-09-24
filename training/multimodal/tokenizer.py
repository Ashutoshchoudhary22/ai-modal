"""Lightweight character tokenizer for development multimodal training."""

from __future__ import annotations

from dataclasses import dataclass

PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
BOS_TOKEN = "<bos>"
EOS_TOKEN = "<eos>"
IGNORE_INDEX = -100


@dataclass
class EncodedText:
    input_ids: list[int]
    labels: list[int]
    attention_mask: list[int]


class CharTokenizer:
    def __init__(self, vocab: dict[str, int] | None = None) -> None:
        self.special_tokens = [PAD_TOKEN, UNK_TOKEN, BOS_TOKEN, EOS_TOKEN]
        if vocab is None:
            self.token_to_id = {token: idx for idx, token in enumerate(self.special_tokens)}
        else:
            self.token_to_id = dict(vocab)
        self.id_to_token = {idx: token for token, idx in self.token_to_id.items()}
        self.pad_token_id = self.token_to_id[PAD_TOKEN]
        self.unk_token_id = self.token_to_id[UNK_TOKEN]
        self.bos_token_id = self.token_to_id[BOS_TOKEN]
        self.eos_token_id = self.token_to_id[EOS_TOKEN]

    @property
    def vocab_size(self) -> int:
        return len(self.token_to_id)

    def build_vocab(self, texts: list[str]) -> None:
        chars = sorted({char for text in texts for char in text})
        next_id = len(self.special_tokens)
        for char in chars:
            if char not in self.token_to_id:
                self.token_to_id[char] = next_id
                next_id += 1
        self.id_to_token = {idx: token for token, idx in self.token_to_id.items()}

    def encode(self, text: str, *, max_length: int) -> list[int]:
        ids = [self.bos_token_id]
        for char in text:
            ids.append(self.token_to_id.get(char, self.unk_token_id))
        ids.append(self.eos_token_id)
        if len(ids) > max_length:
            ids = ids[: max_length - 1] + [self.eos_token_id]
        return ids

    def encode_conversation(
        self,
        formatted_text: str,
        *,
        max_length: int,
        assistant_start: int,
    ) -> EncodedText:
        input_ids = self.encode(formatted_text, max_length=max_length)
        labels = [IGNORE_INDEX] * len(input_ids)
        for idx in range(assistant_start, len(input_ids)):
            labels[idx] = input_ids[idx]
        attention_mask = [1 if token_id != self.pad_token_id else 0 for token_id in input_ids]
        return EncodedText(input_ids=input_ids, labels=labels, attention_mask=attention_mask)

    def pad_batch(
        self,
        batch: list[EncodedText],
    ) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
        max_len = max(len(item.input_ids) for item in batch)
        input_ids: list[list[int]] = []
        labels: list[list[int]] = []
        attention_mask: list[list[int]] = []
        for item in batch:
            pad_count = max_len - len(item.input_ids)
            input_ids.append(item.input_ids + [self.pad_token_id] * pad_count)
            labels.append(item.labels + [IGNORE_INDEX] * pad_count)
            attention_mask.append(item.attention_mask + [0] * pad_count)
        return input_ids, labels, attention_mask

    def to_dict(self) -> dict[str, int]:
        return dict(self.token_to_id)

    @classmethod
    def from_dict(cls, vocab: dict[str, int]) -> CharTokenizer:
        return cls(vocab=vocab)
