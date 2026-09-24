"""Configurable conversation formatting for multimodal training."""

from __future__ import annotations

from training.multimodal.config import ProcessorSection
from training.multimodal.records import MultimodalParsedRecord


def format_conversation(
    record: MultimodalParsedRecord, processor: ProcessorSection
) -> tuple[str, int]:
    parts: list[str] = []
    assistant_start_char = 0
    found_assistant = False

    for message in record.messages:
        role = message["role"]
        content_blocks = message["content"]
        rendered_blocks: list[str] = []
        for block in content_blocks:
            if block["type"] == "text":
                rendered_blocks.append(block["text"])
            elif block["type"] == "image":
                rendered_blocks.append(processor.image_token)
        content = "\n".join(rendered_blocks)
        rendered = processor.chat_template.format(role=role, content=content)
        if role == "assistant" and not found_assistant:
            assistant_start_char = len("".join(parts))
            found_assistant = True
        parts.append(rendered)

    formatted = "".join(parts)
    if not found_assistant:
        assistant_start_char = len(formatted)
    return formatted, assistant_start_char
