"""Validator tests for the synthetic dataset builder."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.dataset.builder import (  # noqa: E402
    DatasetValidationError,
    assign_split,
    fact_in_structured_fields,
    fact_supported_by_text,
    validate_cases,
)

MARKER = "DOCUMENTO SINTÉTICO PARA EVALUACIÓN ACADÉMICA — NO CORRESPONDE A UN CASO REAL"


def _case(case_id: str = "SYN-CHQ-2026-901", source_ids: list[str] | None = None) -> dict:
    source_ids = source_ids or [f"SRC-CHQ-2026-{index}" for index in range(1, 6)]
    return {
        "case_id": case_id,
        "cud": "CUD-SYN-TEST",
        "department": "Chuquisaca",
        "report_date": "2026-10-09",
        "subjects": [
            {
                "name": "Ana Prueba",
                "document_type": "CI",
                "document_number": "1000001",
                "role": "denunciante",
            }
        ],
        "legal_status": None,
        "objective": "Redactar un informe breve.",
        "facts": ["Ana Prueba reportó un hecho."],
        "missing_fields": [],
        "contradictions": [],
        "source_ids": source_ids,
        "evaluation_key": {
            "relevant_source_ids": source_ids[:2],
            "required_facts": ["Ana Prueba reportó un hecho."],
            "source_only_facts": [
                {
                    "fact_id": "F1",
                    "text": "El porton estaba pintado de azul.",
                    "source_id": source_ids[0],
                },
                {
                    "fact_id": "F2",
                    "text": "La inspeccion encontro una pala rota.",
                    "source_id": source_ids[1],
                },
            ],
        },
    }


def _write_sources(directory: Path, case: dict) -> None:
    for source_id in case["source_ids"]:
        body = "Texto general del expediente sintetico."
        if source_id == case["source_ids"][0]:
            body = "El porton estaba pintado de azul durante la visita."
        if source_id == case["source_ids"][1]:
            body = "La inspeccion encontro una pala rota en la zanja."
        text = (
            f"{MARKER}\n\n"
            f"- case_id: {case['case_id']}\n"
            f"- source_id: {source_id}\n\n"
            f"{body}\n"
        )
        (directory / f"{case['case_id']}_{source_id}.md").write_text(text, encoding="utf-8")


def test_valid_case_has_no_errors(tmp_path: Path) -> None:
    case = _case()
    _write_sources(tmp_path, case)
    errors, warnings = validate_cases([case], tmp_path)
    assert errors == []
    assert warnings == []


def test_duplicate_case_id_is_rejected(tmp_path: Path) -> None:
    first = _case()
    second = _case()
    second["source_ids"] = [f"SRC-LPZ-2026-{index}" for index in range(1, 6)]
    second["evaluation_key"]["relevant_source_ids"] = second["source_ids"][:2]
    for item in second["evaluation_key"]["source_only_facts"]:
        item["source_id"] = second["source_ids"][0 if item["fact_id"] == "F1" else 1]
    _write_sources(tmp_path, first)
    _write_sources(tmp_path, second)
    errors, _warnings = validate_cases([first, second], tmp_path)
    assert any("Duplicate case_id" in error for error in errors)


def test_source_count_outside_range_is_rejected(tmp_path: Path) -> None:
    case = _case(source_ids=["SRC-CHQ-2026-1", "SRC-CHQ-2026-2", "SRC-CHQ-2026-3"])
    case["evaluation_key"]["relevant_source_ids"] = case["source_ids"][:2]
    case["evaluation_key"]["source_only_facts"][0]["source_id"] = case["source_ids"][0]
    case["evaluation_key"]["source_only_facts"][1]["source_id"] = case["source_ids"][1]
    _write_sources(tmp_path, case)
    errors, _warnings = validate_cases([case], tmp_path)
    assert any("expected 5 or 6 sources" in error for error in errors)


def test_source_only_fact_copied_into_structured_fields_is_rejected(tmp_path: Path) -> None:
    case = _case()
    case["facts"].append("El porton estaba pintado de azul.")
    _write_sources(tmp_path, case)
    errors, _warnings = validate_cases([case], tmp_path)
    assert any("structured fields" in error for error in errors)


def test_fact_support_and_structured_copy_helpers() -> None:
    assert fact_supported_by_text(
        "El porton estaba pintado de azul.",
        "Durante la visita el porton estaba pintado de azul.",
    )
    assert not fact_supported_by_text(
        "El porton estaba pintado de azul.",
        "Solo se hablo del clima.",
    )
    case = _case()
    assert not fact_in_structured_fields("El porton estaba pintado de azul.", case)
    case["facts"].append("El porton estaba pintado de azul.")
    assert fact_in_structured_fields("El porton estaba pintado de azul.", case)


def test_split_is_stable_disjoint_and_reserves_eight_cases() -> None:
    case_ids = [f"SYN-CHQ-2026-{index:03d}" for index in range(1, 25)]
    first = assign_split(case_ids)
    second = assign_split(list(reversed(case_ids)))
    assert first == second
    assert len(first["development"]) == 16
    assert len(first["test"]) == 8
    assert set(first["development"]).isdisjoint(first["test"])
    assert set(first["development"]) | set(first["test"]) == set(case_ids)


def test_split_rejects_a_corpus_that_cannot_reserve_a_test_set() -> None:
    with pytest.raises(DatasetValidationError):
        assign_split(["SYN-CHQ-2026-001"])
