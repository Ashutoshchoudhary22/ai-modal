"""JSONL record schema for coding SFT datasets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


class InstructionRecord(BaseModel):
    id: str | None = None
    instruction: str
    input: str = ""
    output: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_non_empty_output(self) -> InstructionRecord:
        if not self.output.strip():
            raise ValueError("output must not be empty")
        return self


class MessageRecord(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ConversationalRecord(BaseModel):
    id: str | None = None
    messages: list[MessageRecord] = Field(min_length=2)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_assistant_present(self) -> ConversationalRecord:
        if not any(message.role == "assistant" for message in self.messages):
            raise ValueError("conversational record requires at least one assistant message")
        return self


class CompletionRecord(BaseModel):
    id: str | None = None
    prompt: str
    completion: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_non_empty_completion(self) -> CompletionRecord:
        if not self.completion.strip():
            raise ValueError("completion must not be empty")
        return self


class PreferenceRecord(BaseModel):
    id: str | None = None
    prompt: str
    chosen: str
    rejected: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_preference_pair(self) -> PreferenceRecord:
        if not self.chosen.strip():
            raise ValueError("chosen must not be empty")
        if not self.rejected.strip():
            raise ValueError("rejected must not be empty")
        if self.chosen.strip() == self.rejected.strip():
            raise ValueError("chosen and rejected must differ")
        return self


RecordKind = Literal["instruction", "conversational", "completion", "preference"]


@dataclass
class ParsedRecord:
    line_number: int
    kind: RecordKind
    record_id: str | None
    instruction: str
    input_text: str
    output: str
    messages: list[dict[str, str]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def dedup_key(self) -> str:
        if self.kind == "conversational":
            return json.dumps(self.messages, sort_keys=True, ensure_ascii=False)
        if self.kind == "completion":
            return f"{self.instruction}\n{self.output}"
        if self.kind == "preference":
            return f"{self.instruction}\n{self.input_text}\n{self.output}"
        return f"{self.instruction}\n{self.input_text}\n{self.output}"


def parse_record(line_number: int, payload: dict[str, Any]) -> ParsedRecord:
    if "chosen" in payload and "rejected" in payload:
        record = PreferenceRecord.model_validate(payload)
        return ParsedRecord(
            line_number=line_number,
            kind="preference",
            record_id=record.id,
            instruction=record.prompt,
            input_text=record.rejected,
            output=record.chosen,
            metadata=record.metadata,
            raw=payload,
        )

    if "prompt" in payload and "completion" in payload and "instruction" not in payload:
        record = CompletionRecord.model_validate(payload)
        return ParsedRecord(
            line_number=line_number,
            kind="completion",
            record_id=record.id,
            instruction=record.prompt,
            input_text="",
            output=record.completion,
            metadata=record.metadata,
            raw=payload,
        )

    if "messages" in payload:
        record = ConversationalRecord.model_validate(payload)
        assistant_parts = [m.content for m in record.messages if m.role == "assistant"]
        user_parts = [m.content for m in record.messages if m.role == "user"]
        system_parts = [m.content for m in record.messages if m.role == "system"]
        return ParsedRecord(
            line_number=line_number,
            kind="conversational",
            record_id=record.id,
            instruction=system_parts[0] if system_parts else "",
            input_text="\n".join(user_parts),
            output="\n\n".join(assistant_parts),
            messages=[{"role": m.role, "content": m.content} for m in record.messages],
            metadata=record.metadata,
            raw=payload,
        )

    record = InstructionRecord.model_validate(payload)
    return ParsedRecord(
        line_number=line_number,
        kind="instruction",
        record_id=record.id,
        instruction=record.instruction,
        input_text=record.input,
        output=record.output,
        metadata=record.metadata,
        raw=payload,
    )


def try_parse_record(
    line_number: int,
    payload: dict[str, Any],
) -> tuple[ParsedRecord | None, str | None]:
    try:
        return parse_record(line_number, payload), None
    except (ValidationError, ValueError, TypeError) as exc:
        return None, str(exc)
