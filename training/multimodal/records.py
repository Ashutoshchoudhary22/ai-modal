"""Multimodal training record parsing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from training.datasets.records import ParsedRecord, parse_record, try_parse_record


class TextBlock(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageBlock(BaseModel):
    type: Literal["image"] = "image"
    image: str


ContentBlock = TextBlock | ImageBlock


class MultimodalMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: list[TextBlock | ImageBlock] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_non_empty(self) -> MultimodalMessage:
        if not self.content:
            raise ValueError("message content must not be empty")
        return self


class MultimodalTrainingRecord(BaseModel):
    id: str | None = None
    messages: list[MultimodalMessage] = Field(min_length=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assistant_target(self) -> MultimodalTrainingRecord:
        if not any(message.role == "assistant" for message in self.messages):
            raise ValueError("multimodal record requires assistant target")
        return self


@dataclass
class MultimodalParsedRecord:
    line_number: int
    record_id: str | None
    messages: list[dict[str, Any]]
    image_paths: list[str]
    assistant_text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        return json.dumps(
            {"messages": self.messages, "images": self.image_paths},
            sort_keys=True,
            ensure_ascii=False,
        )


def _is_multimodal_payload(payload: dict[str, Any]) -> bool:
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return False
    for message in messages:
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "image":
                    return True
    return False


def parse_multimodal_record(line_number: int, payload: dict[str, Any]) -> MultimodalParsedRecord:
    record = MultimodalTrainingRecord.model_validate(payload)
    image_paths: list[str] = []
    serialized_messages: list[dict[str, Any]] = []
    assistant_parts: list[str] = []

    for message in record.messages:
        blocks: list[dict[str, Any]] = []
        for block in message.content:
            if isinstance(block, ImageBlock):
                image_paths.append(block.image)
                blocks.append({"type": "image", "image": block.image})
            else:
                blocks.append({"type": "text", "text": block.text})
                if message.role == "assistant":
                    assistant_parts.append(block.text)
        serialized_messages.append({"role": message.role, "content": blocks})

    return MultimodalParsedRecord(
        line_number=line_number,
        record_id=record.id,
        messages=serialized_messages,
        image_paths=image_paths,
        assistant_text="\n".join(assistant_parts),
        metadata=record.metadata,
        raw=payload,
    )


def parse_any_record(
    line_number: int,
    payload: dict[str, Any],
) -> tuple[MultimodalParsedRecord | ParsedRecord, Literal["multimodal", "text"]]:
    if _is_multimodal_payload(payload):
        return parse_multimodal_record(line_number, payload), "multimodal"
    return parse_record(line_number, payload), "text"


def try_parse_any_record(
    line_number: int,
    payload: dict[str, Any],
) -> tuple[MultimodalParsedRecord | ParsedRecord | None, str | None]:
    try:
        record, _ = parse_any_record(line_number, payload)
        return record, None
    except Exception as exc:
        if _is_multimodal_payload(payload):
            return None, str(exc)
        parsed, error = try_parse_record(line_number, payload)
        return parsed, error


def load_jsonl_multimodal(path: Path) -> list[MultimodalParsedRecord]:
    import json

    records: list[MultimodalParsedRecord] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            payload = json.loads(stripped)
            record, kind = parse_any_record(line_number, payload)
            if kind != "multimodal":
                raise ValueError(f"Line {line_number}: expected multimodal record")
            records.append(record)
    return records
