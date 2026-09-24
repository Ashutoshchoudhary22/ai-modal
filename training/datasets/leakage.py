"""Cross-split leakage detection."""

from __future__ import annotations

from dataclasses import dataclass

from training.datasets.dedup import DedupEntry


@dataclass
class LeakageReport:
    train_count: int
    validation_count: int
    test_count: int
    exact_overlap: int
    normalized_overlap: int

    @property
    def passed(self) -> bool:
        return self.exact_overlap == 0 and self.normalized_overlap == 0

    def summary(self) -> str:
        return (
            f"train records: {self.train_count}\n"
            f"validation records: {self.validation_count}\n"
            f"test records: {self.test_count}\n"
            f"cross-split exact overlap: {self.exact_overlap}\n"
            f"cross-split normalized overlap: {self.normalized_overlap}"
        )


def detect_split_leakage(
    train: list[DedupEntry],
    validation: list[DedupEntry],
    test: list[DedupEntry],
) -> LeakageReport:
    train_exact = {e.original_hash for e in train}
    val_exact = {e.original_hash for e in validation}
    test_exact = {e.original_hash for e in test}
    train_norm = {e.normalized_hash for e in train}
    val_norm = {e.normalized_hash for e in validation}
    test_norm = {e.normalized_hash for e in test}

    exact_overlap = len(
        (train_exact & val_exact) | (train_exact & test_exact) | (val_exact & test_exact)
    )
    normalized_overlap = len(
        (train_norm & val_norm) | (train_norm & test_norm) | (val_norm & test_norm)
    )
    return LeakageReport(
        train_count=len(train),
        validation_count=len(validation),
        test_count=len(test),
        exact_overlap=exact_overlap,
        normalized_overlap=normalized_overlap,
    )
