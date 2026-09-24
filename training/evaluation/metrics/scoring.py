"""Metric scoring implementations."""

from __future__ import annotations

import json
import re
from typing import Any


def exact_match(prediction: str, reference: str) -> float:
    return 1.0 if prediction == reference else 0.0


def normalized_match(
    prediction: str,
    reference: str,
    *,
    ignore_case: bool = False,
    collapse_whitespace: bool = True,
    normalize_newlines: bool = True,
) -> float:
    pred = prediction
    ref = reference
    if normalize_newlines:
        pred = pred.replace("\r\n", "\n")
        ref = ref.replace("\r\n", "\n")
    if collapse_whitespace:
        pred = re.sub(r"\s+", " ", pred).strip()
        ref = re.sub(r"\s+", " ", ref).strip()
    if ignore_case:
        pred = pred.lower()
        ref = ref.lower()
    return 1.0 if pred == ref else 0.0


def schema_validity(payload: str | dict[str, Any]) -> float:
    try:
        if isinstance(payload, str):
            json.loads(payload)
        elif isinstance(payload, dict):
            json.dumps(payload)
        else:
            return 0.0
        return 1.0
    except (TypeError, json.JSONDecodeError):
        return 0.0


def field_accuracy(prediction: dict[str, Any], reference: dict[str, Any]) -> float:
    if not reference:
        return 0.0
    matched = 0
    total = 0
    for key, ref_value in reference.items():
        total += 1
        pred_value = prediction.get(key)
        if isinstance(ref_value, dict) and isinstance(pred_value, dict):
            matched += field_accuracy(pred_value, ref_value) * len(ref_value)
            total += len(ref_value) - 1
        elif pred_value == ref_value:
            matched += 1
    return matched / total if total else 0.0


def aggregate_rate(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def median(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 0:
        return (ordered[mid - 1] + ordered[mid]) / 2
    return ordered[mid]
