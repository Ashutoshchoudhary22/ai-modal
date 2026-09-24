"""Training metrics for multimodal runs."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TrainingMetrics:
    step: int
    epoch: int
    loss: float | None = None
    learning_rate: float | None = None
    grad_norm: float | None = None
    throughput: float | None = None
    elapsed_time: float | None = None
    samples_per_second: float | None = None
    tokens_per_second: float | None = None
    image_count: int | None = None
    validation_loss: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetricsTracker:
    def __init__(self) -> None:
        self.started_at = time.perf_counter()
        self.history: list[TrainingMetrics] = []

    def record(self, metrics: TrainingMetrics) -> None:
        metrics.elapsed_time = time.perf_counter() - self.started_at
        self.history.append(metrics)

    def summary(self) -> dict[str, Any]:
        if not self.history:
            return {}
        last = self.history[-1]
        return {
            "steps": last.step,
            "epochs": last.epoch,
            "last_loss": last.loss,
            "last_validation_loss": last.validation_loss,
            "elapsed_time": last.elapsed_time,
        }
