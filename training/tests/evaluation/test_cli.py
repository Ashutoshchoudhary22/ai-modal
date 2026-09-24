from training.evaluation.cli import main


def test_list_benchmarks():
    assert main(["list-benchmarks"]) == 0


def test_validate_coding_mini():
    assert main(["validate", "--benchmark", "coding-mini"]) == 0
