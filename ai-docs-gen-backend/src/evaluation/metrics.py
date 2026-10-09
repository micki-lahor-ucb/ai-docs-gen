"""Aggregate human labels. Missing labels are never treated as a pass."""

from __future__ import annotations

import math
import re

CRITICAL = ("fidelity", "no_invention", "verifiable_sources", "missing_handled")
REQUIRED_FOR_ACCEPTANCE = CRITICAL + ("completeness",)
COMPLEMENTARY = ("pertinence", "format")
ALL_CRITERIA = REQUIRED_FOR_ACCEPTANCE + COMPLEMENTARY
Z_95 = 1.96


def wilson_interval(successes: int, total: int, z: float = Z_95) -> tuple[float, float] | None:
    """Wilson score interval for a proportion. None when there is no sample."""
    if total <= 0:
        return None
    if successes < 0 or successes > total:
        raise ValueError("successes must be between 0 and total")
    center = (successes + z * z / 2) / (total + z * z)
    margin = z * math.sqrt(successes * (total - successes) / total + z * z / 4) / (total + z * z)
    return (max(0.0, center - margin), min(1.0, center + margin))


def proportion(successes: int, total: int) -> float | None:
    """Return k/n, or None when the denominator is zero."""
    if total <= 0:
        return None
    return successes / total


def is_accepted(row: dict) -> bool | None:
    """A draft is accepted only when every required criterion passed."""
    values = [normalize_label(row.get(name)) for name in REQUIRED_FOR_ACCEPTANCE]
    if any(value is None for value in values):
        return None
    return all(values)


def critical_passed(row: dict) -> bool | None:
    """Whether the four critical criteria passed, even if completeness failed."""
    values = [normalize_label(row.get(name)) for name in CRITICAL]
    if any(value is None for value in values):
        return None
    return all(values)


def normalize_label(value: object) -> bool | None:
    """Map a human label to pass or fail. Blank means unlabeled."""
    if value is None:
        return None
    text = str(value).strip().lower()
    if text in {"", "pendiente"}:
        return None
    if text in {"pass", "si", "sí", "aprobado", "true", "1"}:
        return True
    if text in {"fail", "no", "reprobado", "false", "0"}:
        return False
    raise ValueError(f"Etiqueta no reconocida: {value}")


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _lcs_length(left: list[str], right: list[str]) -> int:
    previous = [0] * (len(right) + 1)
    for token in left:
        current = [0]
        for index, other in enumerate(right, start=1):
            if token == other:
                current.append(previous[index - 1] + 1)
            else:
                current.append(max(previous[index], current[-1]))
        previous = current
    return previous[-1]


def rouge_l(hypothesis: str, reference: str) -> float | None:
    """Exploratory ROUGE-L F1. It does not measure factual truth."""
    left = _tokens(hypothesis)
    right = _tokens(reference)
    if not left or not right:
        return None
    common = _lcs_length(left, right)
    precision = common / len(left)
    recall = common / len(right)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def recall_at_k(retrieved: list[str], relevant: list[str], k: int = 3) -> float | None:
    """Fraction of relevant sources present in the first k retrieved ids."""
    if not relevant:
        return None
    found = set(retrieved[:k])
    return len(set(relevant) & found) / len(set(relevant))


def reference_text(gold: dict) -> str:
    """Build the exploratory reference from required and source-only facts."""
    parts = list(gold.get("required_facts") or [])
    for fact in gold.get("source_only_facts") or []:
        parts.append(fact.get("text") or "")
    return " ".join(part for part in parts if part)
