"""Template tests for complete cases, missing fields and similar names."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.baseline.template_generator import PENDING, generate_baseline  # noqa: E402
from src.retrieval.tfidf import RetrievedSource  # noqa: E402


def _case(**overrides) -> dict:
    case = {
        "case_id": "SYN-CHQ-2026-900",
        "cud": "CUD-SYN-900",
        "department": "Chuquisaca",
        "report_date": "2026-10-09",
        "subjects": [
            {
                "name": "Ana Prado",
                "document_type": "CI",
                "document_number": "100",
                "role": "denunciante",
            }
        ],
        "legal_status": "Dato expreso en una fuente",
        "objective": "Dejar constancia del hecho.",
        "facts": ["Ana Prado reportó el hecho el 1 de mayo."],
        "missing_fields": [],
        "contradictions": [],
    }
    case.update(overrides)
    return case


def test_complete_case_copies_fields_and_pastes_excerpt() -> None:
    excerpt = "El porton azul fue hallado abierto el martes."
    draft = generate_baseline(
        _case(),
        [RetrievedSource("SRC-1", f"DOCUMENTO\n\n- source_id: SRC-1\n\n{excerpt}\n", 0.5)],
    )
    assert "SYN-CHQ-2026-900" in draft
    assert "CUD-SYN-900" in draft
    assert "Ana Prado reportó el hecho el 1 de mayo." in draft
    assert "### Fuente: SRC-1" in draft
    assert excerpt in draft
    assert "Dato expreso en una fuente" in draft


def test_missing_fields_are_marked_pending() -> None:
    draft = generate_baseline(
        _case(legal_status=None, facts=[], missing_fields=["Plano del predio"]),
        [],
    )
    assert draft.count(PENDING) >= 2
    assert "Plano del predio" in draft
    assert "Situación jurídica: " + PENDING in draft


def test_similar_names_are_copied_without_being_merged() -> None:
    draft = generate_baseline(
        _case(
            subjects=[
                {
                    "name": "Juan Carlos Medina",
                    "document_type": "CI",
                    "document_number": "111",
                    "role": "denunciante",
                },
                {
                    "name": "Juan Carlos Mamani",
                    "document_type": "CI",
                    "document_number": "222",
                    "role": "denunciado",
                },
            ]
        ),
        [],
    )
    assert "Juan Carlos Medina" in draft
    assert "Juan Carlos Mamani" in draft
    assert "CI 111" in draft
    assert "CI 222" in draft
