"""Stratified train/val/test splitting for RareArena cases.

Splits are stratified by disease (Orpha_id) so each disease's cases
are distributed across train/val/test. Diseases with fewer than 3 cases
go entirely to train to avoid data leakage from tiny eval sets.
"""

import logging
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from rare_archive_datasets.ingestion.rarearena import RareArenaCase

logger = logging.getLogger(__name__)


@dataclass
class SplitResult:
    """Result of splitting a case collection."""
    train: list[RareArenaCase]
    val: list[RareArenaCase]
    test: list[RareArenaCase]
    stats: dict[str, Any]


def stratified_split(
    cases: list[RareArenaCase],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    min_cases_for_split: int = 3,
    seed: int = 42,
) -> SplitResult:
    """Split cases into train/val/test, stratified by disease_id.

    Args:
        cases: All cases to split
        train_ratio: Fraction for training
        val_ratio: Fraction for validation
        test_ratio: Fraction for test
        min_cases_for_split: Diseases with fewer cases go entirely to train
        seed: Random seed for reproducibility
    """
    rng = random.Random(seed)

    # Group cases by disease_id (or diagnosis string as fallback)
    groups: dict[str, list[RareArenaCase]] = defaultdict(list)
    for case in cases:
        key = case.disease_id or case.ground_truth_diagnosis or "unknown"
        groups[key].append(case)

    train, val, test = [], [], []
    small_disease_count = 0

    for disease_key, disease_cases in groups.items():
        rng.shuffle(disease_cases)

        if len(disease_cases) < min_cases_for_split:
            # Too few cases — all go to train
            train.extend(disease_cases)
            small_disease_count += 1
            continue

        n = len(disease_cases)
        n_val = max(1, round(n * val_ratio))
        n_test = max(1, round(n * test_ratio))
        n_train = n - n_val - n_test

        train.extend(disease_cases[:n_train])
        val.extend(disease_cases[n_train:n_train + n_val])
        test.extend(disease_cases[n_train + n_val:])

    # Shuffle within each split
    rng.shuffle(train)
    rng.shuffle(val)
    rng.shuffle(test)

    stats = {
        "total_cases": len(cases),
        "train": len(train),
        "val": len(val),
        "test": len(test),
        "unique_diseases": len(groups),
        "small_diseases_train_only": small_disease_count,
    }

    logger.info(
        f"Split {len(cases)} cases: "
        f"train={len(train)}, val={len(val)}, test={len(test)} "
        f"({len(groups)} diseases, {small_disease_count} train-only)"
    )

    return SplitResult(train=train, val=val, test=test, stats=stats)
