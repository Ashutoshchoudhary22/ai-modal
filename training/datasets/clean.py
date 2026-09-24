"""Deterministic dataset cleaning."""

from __future__ import annotations

import unicodedata

from training.datasets.manifest import DatasetManifest, PreprocessingConfig
from training.datasets.records import ParsedRecord


def normalize_unicode(text: str, form: str) -> str:
    if form == "none":
        return text
    return unicodedata.normalize(form, text)


def clean_record(record: ParsedRecord, config: PreprocessingConfig) -> ParsedRecord | None:
    instruction = record.instruction
    input_text = record.input_text
    output = record.output
    messages = list(record.messages)

    if config.unicode_normalize != "none":
        instruction = normalize_unicode(instruction, config.unicode_normalize)
        input_text = normalize_unicode(input_text, config.unicode_normalize)
        output = normalize_unicode(output, config.unicode_normalize)
        messages = [
            {
                "role": message["role"],
                "content": normalize_unicode(message["content"], config.unicode_normalize),
            }
            for message in messages
        ]

    if config.strip_outer_whitespace:
        instruction = instruction.strip()
        input_text = input_text.strip()
        output = output.strip()
        messages = [
            {"role": message["role"], "content": message["content"].strip()}
            for message in messages
        ]

    if config.remove_empty and not output.strip():
        return None

    max_chars = config.max_chars
    if max_chars is not None:
        combined = f"{instruction}\n{input_text}\n{output}"
        if len(combined) > max_chars:
            return None

    return ParsedRecord(
        line_number=record.line_number,
        kind=record.kind,
        record_id=record.record_id,
        instruction=instruction,
        input_text=input_text,
        output=output,
        messages=messages,
        metadata=dict(record.metadata),
        raw=dict(record.raw),
    )


def clean_records(
    records: list[ParsedRecord],
    manifest: DatasetManifest,
) -> tuple[list[ParsedRecord], list[str]]:
    cleaned: list[ParsedRecord] = []
    rejected: list[str] = []
    config = manifest.preprocessing
    if config.max_chars is None:
        config = config.model_copy(update={"max_chars": manifest.quality.max_chars})

    for record in records:
        result = clean_record(record, config)
        if result is None:
            rejected.append(f"line {record.line_number}: removed by cleaning rules")
            continue
        cleaned.append(result)
    return cleaned, rejected
