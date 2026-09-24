from training.datasets.dedup import deduplicate_records
from training.datasets.manifest import SplitConfig
from training.datasets.records import parse_record
from training.datasets.split import split_records


def test_split_is_deterministic_and_disjoint():
    records = [
        parse_record(i, {"instruction": f"t{i}", "input": "", "output": f"out{i}"})
        for i in range(1, 11)
    ]
    entries = deduplicate_records(records).kept
    first = split_records(entries, SplitConfig(train=0.8, validation=0.1, test=0.1, seed=42))
    second = split_records(entries, SplitConfig(train=0.8, validation=0.1, test=0.1, seed=42))
    assert [e.normalized_hash for e in first.train] == [e.normalized_hash for e in second.train]
    assert len(first.train) + len(first.validation) + len(first.test) == len(entries)
