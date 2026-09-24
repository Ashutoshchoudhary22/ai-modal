"""Completion evaluator tests."""

from training.evaluation.adapters.development import DevelopmentEvaluationAdapter
from training.evaluation.evaluators.completion import evaluate_completion_sample
from training.evaluation.types import GenerationConfig


def test_completion_evaluator_exact_match() -> None:
    adapter = DevelopmentEvaluationAdapter()
    sample = {
        "id": "comp-1",
        "language": "typescript",
        "prefix": "const user = await db.",
        "suffix": "",
        "expected_completion": "findById(id);",
    }
    result = evaluate_completion_sample(
        sample,
        adapter=adapter,
        generation=GenerationConfig(),
    )
    assert result.status == "completed"
    assert result.metrics["exact_match"] == 1.0
