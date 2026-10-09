"""Generation tests. The local model is replaced by a fake HTTP transport."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.dataset.store import development_ids, load_case_sources, load_cases  # noqa: E402
from src.generation.generator import (  # noqa: E402
    generate_rag,
    strip_thinking,
    unknown_citation_warnings,
)
from src.generation.ollama_client import OllamaClient  # noqa: E402
from src.retrieval.tfidf import retrieve, build_query  # noqa: E402

DATA_DIR = BACKEND_ROOT / "data" / "synthetic"


def _client(handler) -> OllamaClient:
    return OllamaClient(transport=httpx.MockTransport(handler))


def _ok(content: str):
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        assert body["think"] is False
        assert body["stream"] is False
        assert body["model"] == "qwen3.5:4b"
        assert body["options"]["temperature"] == 0
        assert body["options"]["seed"] == 42
        assert body["options"]["num_ctx"] == 4096
        assert request.url.path == "/api/chat"
        return httpx.Response(200, json={"model": "qwen3.5:4b", "message": {"content": content}})

    return handler


def test_mocked_call_records_model_and_strips_thinking() -> None:
    case = {
        "case_id": "SYN-CHQ-2026-900",
        "cud": "CUD-SYN-900",
        "department": "Chuquisaca",
        "report_date": "2026-10-09",
        "subjects": [{"name": "Ana Prado", "document_type": "CI", "document_number": "100", "role": "denunciante"}],
        "legal_status": None,
        "objective": "Dejar constancia.",
        "facts": ["Ana Prado reportó el hecho."],
        "missing_fields": ["Plano del predio"],
        "contradictions": [],
        "source_ids": ["SRC-1"],
    }
    documents = [__import__("src.retrieval.tfidf", fromlist=["SourceDocument"]).SourceDocument("SRC-1", "Texto del caso.")]
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return _ok("<think>razonamiento</think>\n# Informe\nEl hecho consta. [Fuente: SRC-1]")(request)

    result = generate_rag(case, documents, _client(handler))
    sent = json.dumps(captured["body"], ensure_ascii=False)
    assert "Plano del predio" in sent
    assert "No inventes hechos" in sent
    assert result.model == "qwen3.5:4b"
    assert "razonamiento" not in result.draft_markdown
    assert result.warnings == []
    assert result.retrieved_source_ids == ["SRC-1"]


def test_unknown_citation_is_warned_but_not_treated_as_verified() -> None:
    warnings = unknown_citation_warnings("Hecho. [Fuente: SRC-CHQ-2026-999]", {"SRC-CHQ-2026-001"})
    assert len(warnings) == 1
    assert "no se considera verificable" in warnings[0]
    assert unknown_citation_warnings("Hecho. [Fuente: SRC-CHQ-2026-001]", {"SRC-CHQ-2026-001"}) == []


def test_strip_thinking_removes_the_block() -> None:
    assert strip_thinking("<think>oculto</think>\nBorrador") == "Borrador"


def test_unavailable_model_returns_a_readable_warning() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    case = {
        "case_id": "SYN-CHQ-2026-900",
        "objective": "Hecho",
        "facts": ["Un hecho conocido."],
        "subjects": [],
        "missing_fields": [],
        "contradictions": [],
        "legal_status": None,
        "cud": "CUD",
        "department": "Chuquisaca",
        "report_date": "2026-10-09",
    }
    documents = [__import__("src.retrieval.tfidf", fromlist=["SourceDocument"]).SourceDocument("SRC-1", "Texto.")]
    result = generate_rag(case, documents, _client(handler))
    assert result.draft_markdown == ""
    assert "no está disponible" in result.warnings[0]


def test_http_error_and_empty_reply_are_readable() -> None:
    def http_error(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    case = {
        "case_id": "SYN-CHQ-2026-901",
        "objective": "Hecho",
        "facts": ["Un hecho conocido."],
        "subjects": [],
        "missing_fields": ["Dato ausente"],
        "contradictions": [],
        "legal_status": None,
        "cud": "CUD",
        "department": "Chuquisaca",
        "report_date": "2026-10-09",
    }
    documents = [__import__("src.retrieval.tfidf", fromlist=["SourceDocument"]).SourceDocument("SRC-1", "Texto del hecho.")]
    failed = generate_rag(case, documents, _client(http_error))
    assert "HTTP 500" in failed.warnings[0]
    assert failed.draft_markdown == ""

    empty = generate_rag(case, documents, _client(_ok("   ")))
    assert "vacía" in empty.warnings[0]


def test_development_case_keeps_both_relevant_sources() -> None:
    """A development distractor must not push out both relevant sources."""
    gold = {
        json.loads(line)["case_id"]: json.loads(line)
        for line in (DATA_DIR / "gold_labels.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    cases = load_cases()
    found = False
    for case_id in development_ids():
        case = cases[case_id]
        relevant = set(gold[case_id]["relevant_source_ids"])
        selected = {item.source_id for item in retrieve(load_case_sources(case), build_query(case))}
        distractors = set(case["source_ids"]) - relevant
        if relevant <= selected and distractors:
            found = True
            break
    assert found
