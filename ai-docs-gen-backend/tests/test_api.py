"""API tests. The local model is replaced except where a test says otherwise."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import backend.main as api  # noqa: E402
from src.generation.ollama_client import OllamaError, OllamaReply  # noqa: E402

CLIENT = TestClient(api.app, raise_server_exceptions=False)


class FakeClient:
    """Stand-in used only by tests."""

    def __init__(self, reply: str | None = "Borrador de prueba. [Fuente: SRC-CHQ-2026-001]", fail: str | None = None) -> None:
        self.reply = reply
        self.fail = fail
        self.calls = 0

    def chat(self, messages: list[dict]) -> OllamaReply:
        self.calls += 1
        if self.fail:
            raise OllamaError(self.fail)
        return OllamaReply(content=self.reply or "", model="qwen3.5:4b")

    def close(self) -> None:
        return None


@pytest.fixture
def fake_client(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(api, "make_ollama_client", lambda: client)
    return client


def test_frontend_is_served_without_hiding_docs() -> None:
    page = CLIENT.get("/")
    assert page.status_code == 200
    assert "Asistente de redacción" in page.text
    assert "requiere revisión humana" in page.text
    script = CLIENT.get("/static/app.js")
    assert script.status_code == 200
    assert "innerHTML" not in script.text
    docs = CLIENT.get("/docs")
    assert docs.status_code == 200
    health = CLIENT.get("/api/health")
    assert health.status_code == 200
    response = CLIENT.get("/docs")
    assert response.status_code == 200
    spec = CLIENT.get("/openapi.json")
    paths = spec.json()["paths"]
    assert "/api/health" in paths
    assert "/api/cases" in paths
    assert "/api/cases/{case_id}" in paths
    assert "/api/generate" in paths


def test_valid_case_copies_known_facts(fake_client: FakeClient) -> None:
    response = CLIENT.post("/api/generate", json={"case_id": "SYN-CHQ-2026-010", "method": "baseline"})
    assert response.status_code == 200
    draft = response.json()["draft_markdown"]
    assert "SYN-CHQ-2026-010" in draft
    assert "tractor verde" in draft
    assert "[PENDIENTE: información no proporcionada]" in draft
    assert fake_client.calls == 0


def test_hard_case_keeps_the_contradiction_and_the_missing_fields(fake_client: FakeClient) -> None:
    response = CLIENT.post("/api/generate", json={"case_id": "SYN-BEN-2026-008", "method": "baseline"})
    assert response.status_code == 200
    draft = response.json()["draft_markdown"]
    assert "Informe médico forense" in draft
    assert "Prueba de alcoholemia" in draft
    assert "no coinciden en la hora del incidente" in draft
    assert "Samuel Quiroga" in draft
    assert "Teresa Mendiola" in draft


def test_end_to_end_baseline_flow(fake_client: FakeClient) -> None:
    listed = CLIENT.get("/api/cases")
    assert listed.status_code == 200
    assert any(item["case_id"] == "SYN-CHQ-2026-010" for item in listed.json())
    loaded = CLIENT.get("/api/cases/SYN-CHQ-2026-010")
    assert loaded.status_code == 200
    generated = CLIENT.post("/api/generate", json={"case_id": loaded.json()["case_id"], "method": "baseline"})
    assert generated.status_code == 200
    assert generated.json()["model"] == "template"
    assert fake_client.calls == 0


@pytest.mark.integration
def test_end_to_end_rag_calls_the_local_model() -> None:
    response = CLIENT.post("/api/generate", json={"case_id": "SYN-CHQ-2026-010", "method": "rag"})
    assert response.status_code == 200
    body = response.json()
    assert body["model"] == "qwen3.5:4b"
    assert body["draft_markdown"].strip()
    assert body["retrieved_sources"]
    assert all(source_id.startswith("SRC-CHQ-2026-") for source_id in body["retrieved_sources"])


def test_unknown_case_is_not_found(fake_client: FakeClient) -> None:
    response = CLIENT.get("/api/cases/SYN-CHQ-2026-999")
    assert response.status_code == 404
    generated = CLIENT.post("/api/generate", json={"case_id": "SYN-CHQ-2026-999", "method": "baseline"})
    assert generated.status_code == 404
    assert "Traceback" not in generated.text


def test_invalid_input_is_rejected(fake_client: FakeClient) -> None:
    response = CLIENT.post("/api/generate", json={"case_id": "not-a-case", "method": "magic"})
    assert response.status_code == 422
    extra = CLIENT.post(
        "/api/generate",
        json={"case_id": "SYN-CHQ-2026-001", "method": "baseline", "model_url": "http://example.invalid"},
    )
    assert extra.status_code == 422


def test_edited_fact_is_used_and_sources_stay_on_the_case(fake_client: FakeClient) -> None:
    response = CLIENT.post(
        "/api/generate",
        json={
            "case_id": "SYN-CHQ-2026-001",
            "method": "baseline",
            "facts": ["Hecho editado solo para esta demostración."],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "Hecho editado solo para esta demostración." in body["draft_markdown"]
    assert all(source_id.startswith("SRC-CHQ-2026-") for source_id in body["retrieved_sources"])


def test_ollama_failure_is_a_service_error_without_a_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api, "make_ollama_client", lambda: FakeClient(fail="El modelo local no está disponible. Compruebe que Ollama esté en ejecución."))
    response = CLIENT.post("/api/generate", json={"case_id": "SYN-CHQ-2026-001", "method": "rag"})
    assert response.status_code == 503
    assert "Traceback" not in response.text
    assert "no está disponible" in response.json()["detail"]


def test_unexpected_error_hides_the_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode():
        raise RuntimeError("secret path D:/private")

    monkeypatch.setattr(api, "load_cases", explode)
    response = CLIENT.get("/api/cases")
    assert response.status_code == 500
    assert "secret path" not in response.text
    assert response.json()["detail"] == "Error interno del servidor."
