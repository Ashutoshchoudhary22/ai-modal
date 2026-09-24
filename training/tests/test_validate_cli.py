from training.datasets.validate import main


def test_validate_cli_success(capsys):
    code = main(
        [
            "--input",
            "training/tests/fixtures/smoke_sft.jsonl",
            "--manifest",
            "training/data/manifests/smoke_sft.json",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "Valid records: 10" in captured.out
