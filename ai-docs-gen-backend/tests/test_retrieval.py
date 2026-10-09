"""Retrieval tests. Relevance labels are not used to choose sources."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.retrieval.tfidf import SourceDocument, build_query, retrieve  # noqa: E402


def test_distractor_does_not_displace_documents_that_share_the_query() -> None:
    documents = [
        SourceDocument("SRC-A", "Informe sobre el lindero del terreno agrícola y la cerca movida."),
        SourceDocument("SRC-B", "Inspección del lindero del terreno agrícola y los postes desplazados."),
        SourceDocument("SRC-C", "Factura de agua potable del mes de enero sin relación con el predio."),
        SourceDocument("SRC-D", "Circular de feriados para el personal de recepción."),
        SourceDocument("SRC-E", "Cierre de un caso de hurto de bicicleta en el mercado."),
    ]
    query = "Informe sobre el lindero del terreno agrícola"
    selected = retrieve(documents, query, top_k=3)
    selected_ids = [item.source_id for item in selected]
    assert len(selected_ids) == 3
    assert "SRC-A" in selected_ids
    assert "SRC-B" in selected_ids
    assert "SRC-OTHER-CASE" not in selected_ids


def test_retrieval_uses_only_the_documents_it_receives() -> None:
    documents = [
        SourceDocument("SRC-1", "colisión de un vehículo en la avenida"),
        SourceDocument("SRC-2", "el vehículo azul impactó en la avenida"),
    ]
    selected = retrieve(documents, "colisión de un vehículo en la avenida", top_k=3)
    assert [item.source_id for item in selected] == ["SRC-1", "SRC-2"]


def test_query_uses_objective_and_facts_only() -> None:
    case = {
        "objective": "Documentar el lindero.",
        "facts": ["La cerca fue movida."],
        "subjects": [{"name": "Nombre que no debe entrar en la consulta"}],
    }
    query = build_query(case)
    assert "lindero" in query
    assert "cerca" in query
    assert "Nombre que no debe entrar" not in query
