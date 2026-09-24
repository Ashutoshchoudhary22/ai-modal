from training.evaluation.metrics.scoring import (
    exact_match,
    field_accuracy,
    normalized_match,
    schema_validity,
)


def test_exact_match():
    assert exact_match("hello", "hello") == 1.0
    assert exact_match("hello", "world") == 0.0


def test_normalized_match_whitespace():
    assert normalized_match("a  b", "a b", collapse_whitespace=True) == 1.0


def test_schema_validity():
    assert schema_validity('{"a": 1}') == 1.0
    assert schema_validity("{bad") == 0.0


def test_field_accuracy_partial():
    score = field_accuracy({"a": 1, "b": 2}, {"a": 1, "b": 3})
    assert 0.0 < score < 1.0
