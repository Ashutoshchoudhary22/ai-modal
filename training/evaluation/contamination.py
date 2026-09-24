"""Training/evaluation dataset contamination checks."""

from __future__ import annotations


def check_contamination(
    training_fingerprint: str | None,
    evaluation_fingerprint: str,
) -> list[str]:
    warnings: list[str] = []
    if training_fingerprint and training_fingerprint == evaluation_fingerprint:
        warnings.append(
            "BENCHMARK_CONTAMINATION_WARNING: evaluation fingerprint matches training fingerprint"
        )
    return warnings
