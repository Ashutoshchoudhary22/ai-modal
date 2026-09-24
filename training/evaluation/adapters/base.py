"""Evaluation model adapter protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from training.evaluation.types import GenerationConfig


@dataclass
class ModelCapabilities:
    provider_id: str
    model_id: str
    modalities: list[str] = field(default_factory=lambda: ["text"])
    supports_structured: bool = False
    supports_multimodal: bool = False
    supports_agent: bool = False
    supports_browser: bool = False
    supports_render: bool = False


@dataclass
class GenerationResult:
    text: str
    structured: dict[str, Any] | None = None
    latency_ms: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None


class EvaluationModelAdapter(ABC):
    @abstractmethod
    def capabilities(self) -> ModelCapabilities: ...

    @abstractmethod
    def generate(
        self, prompt: str, *, config: GenerationConfig, sample: dict[str, Any]
    ) -> GenerationResult: ...

    def generate_structured(
        self,
        prompt: str,
        *,
        config: GenerationConfig,
        sample: dict[str, Any],
        schema: dict[str, Any] | None = None,
    ) -> GenerationResult:
        return self.generate(prompt, config=config, sample=sample)

    def multimodal_generate(
        self,
        sample: dict[str, Any],
        *,
        config: GenerationConfig,
        dataset_root: Path,
    ) -> GenerationResult:
        raise NotImplementedError

    def agent_execute(
        self, sample: dict[str, Any], *, config: GenerationConfig, workspace: Path
    ) -> GenerationResult:
        raise NotImplementedError

    def browser_execute(
        self, sample: dict[str, Any], *, config: GenerationConfig, workspace: Path
    ) -> GenerationResult:
        raise NotImplementedError

    def complete(self, request: Any, *, config: GenerationConfig) -> GenerationResult:
        raise NotImplementedError
