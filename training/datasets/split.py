"""Deterministic train/validation/test splitting."""

from __future__ import annotations

import random
from dataclasses import dataclass

from training.datasets.dedup import DedupEntry
from training.datasets.manifest import SplitConfig


@dataclass
class SplitResult:
    train: list[DedupEntry]
    validation: list[DedupEntry]
    test: list[DedupEntry]


def split_records(entries: list[DedupEntry], config: SplitConfig) -> SplitResult:
    if not entries:
        return SplitResult(train=[], validation=[], test=[])

    shuffled = list(entries)
    random.Random(config.seed).shuffle(shuffled)

    total = len(shuffled)
    train_count = int(total * config.train)
    val_count = int(total * config.validation)
    test_count = total - train_count - val_count

    if config.test > 0 and test_count == 0 and total >= 3:
        test_count = 1
        if train_count > 1:
            train_count -= 1

    train = shuffled[:train_count]
    validation = shuffled[train_count : train_count + val_count]
    test = shuffled[train_count + val_count : train_count + val_count + test_count]

    train_hashes = {entry.normalized_hash for entry in train}
    val_hashes = {entry.normalized_hash for entry in validation}
    test_hashes = {entry.normalized_hash for entry in test}
    overlap = (
        (train_hashes & val_hashes)
        | (train_hashes & test_hashes)
        | (val_hashes & test_hashes)
    )
    if overlap:
        raise ValueError("Split produced overlapping records across partitions")

    return SplitResult(train=train, validation=validation, test=test)
