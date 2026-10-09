"""Unit tests for proportions and the Wilson interval."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.evaluation.metrics import (  # noqa: E402
    critical_passed,
    is_accepted,
    proportion,
    recall_at_k,
    rouge_l,
    wilson_interval,
)


def test_wilson_bounds_a_small_sample() -> None:
    low, high = wilson_interval(3, 8)
    assert 0 <= low <= 3 / 8 <= high <= 1


def test_wilson_rejects_an_impossible_count() -> None:
    with pytest.raises(ValueError):
        wilson_interval(9, 8)


def test_proportion_is_none_without_labels() -> None:
    assert proportion(0, 0) is None
    assert proportion(1, 4) == 0.25


def test_acceptance_requires_every_required_criterion() -> None:
    complete = {
        "fidelity": "pass",
        "no_invention": "pass",
        "verifiable_sources": "pass",
        "missing_handled": "pass",
        "completeness": "pass",
        "pertinence": "fail",
        "format": "fail",
    }
    assert is_accepted(complete) is True
    assert critical_passed({**complete, "completeness": "fail"}) is True
    assert is_accepted({**complete, "completeness": "fail"}) is False
    assert is_accepted({**complete, "fidelity": ""}) is None


def test_recall_and_rouge_are_defined() -> None:
    assert recall_at_k(["A", "B", "C"], ["A", "D"]) == 0.5
    score = rouge_l("el porton azul", "porton azul")
    assert score is not None and score > 0
