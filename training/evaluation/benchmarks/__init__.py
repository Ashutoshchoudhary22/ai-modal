"""Benchmark registry."""

from training.evaluation.benchmarks.registry import (
    get,
    list_benchmarks,
    register_builtin_benchmarks,
    validate_benchmark,
)

__all__ = ["get", "list_benchmarks", "register_builtin_benchmarks", "validate_benchmark"]
