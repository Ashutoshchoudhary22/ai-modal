
from training.datasets.dedup import deduplicate_records
from training.datasets.records import parse_record


def test_deduplicate_exact_and_normalized():
    records = [
        parse_record(1, {"instruction": "A", "input": "", "output": "print('x')"}),
        parse_record(2, {"instruction": "A", "input": "", "output": "print('x')"}),
        parse_record(3, {"instruction": "A", "input": "", "output": "print( 'x' )"}),
    ]
    result = deduplicate_records(records)
    assert len(result.kept) == 1
    assert len(result.removed) == 2
