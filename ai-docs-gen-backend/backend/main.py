"""FastAPI application. The model URL is fixed inside the local client."""

from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.schemas import CaseSummary, GenerateRequest, GenerateResponse, HealthResponse
from src.baseline.template_generator import generate_baseline
from src.dataset.store import load_case_sources, load_cases
from src.generation.config import MODEL_NAME, OLLAMA_BASE_URL
from src.generation.generator import generate_rag
from src.generation.ollama_client import OllamaClient
from src.retrieval.tfidf import build_query, retrieve

BACKEND_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BACKEND_ROOT.parent / "ai-docs-gen-frontend"
INDEX_PATH = FRONTEND_DIR / "index.html"

app = FastAPI(title="Informe breve de antecedentes", version="1.0.0")
if FRONTEND_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="frontend-static")


def make_ollama_client() -> OllamaClient:
    """Create the production client. Tests replace this function."""
    return OllamaClient()


def apply_edits(stored: dict, request: GenerateRequest) -> dict:
    """Use edited fields, but keep the sources of the stored case."""
    case = deepcopy(stored)
    supplied = request.model_dump(exclude_unset=True)
    for key in ("objective", "facts", "missing_fields", "contradictions", "legal_status", "subjects"):
        if key in supplied:
            case[key] = supplied[key]
    case["source_ids"] = list(stored["source_ids"])
    case["case_id"] = stored["case_id"]
    return case


def ollama_status() -> str:
    """Check the local model without returning its full tag payload."""
    try:
        response = httpx.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2.0)
        response.raise_for_status()
        names = [item.get("name") for item in response.json().get("models", [])]
    except httpx.HTTPError:
        return "unavailable"
    if MODEL_NAME in names:
        return "available"
    return "model_missing"


@app.exception_handler(Exception)
def unhandled_error(request, error: Exception) -> JSONResponse:  # noqa: ARG001
    """Hide unexpected failures from the browser."""
    if isinstance(error, HTTPException):
        raise error
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor."})


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report whether the local model can be reached."""
    return HealthResponse(status="ok", ollama=ollama_status(), model=MODEL_NAME)


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases() -> list[CaseSummary]:
    """List stored synthetic cases. Gold labels are not included."""
    cases = load_cases()
    return [
        CaseSummary(
            case_id=case["case_id"],
            department=case["department"],
            objective=case["objective"],
        )
        for case in sorted(cases.values(), key=lambda item: item["case_id"])
    ]


@app.get("/api/cases/{case_id}")
def get_case(case_id: str) -> dict:
    """Return one structured case. Evaluation keys are not stored here."""
    case = load_cases().get(case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    return case


@app.post("/api/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    """Run the template or the local model on one stored case."""
    if not request.text_fields_are_bounded():
        raise HTTPException(status_code=422, detail="Un campo de texto supera el tamaño permitido.")
    stored = load_cases().get(request.case_id)
    if stored is None:
        raise HTTPException(status_code=404, detail="Caso no encontrado.")
    case = apply_edits(stored, request)
    documents = load_case_sources(case)
    warnings: list[str] = []
    if not case.get("legal_status"):
        warnings.append("La situación jurídica no fue proporcionada.")
    if request.method == "baseline":
        started = time.perf_counter()
        excerpts = retrieve(documents, build_query(case))
        draft = generate_baseline(case, excerpts)
        elapsed = int((time.perf_counter() - started) * 1000)
        return GenerateResponse(
            case_id=case["case_id"],
            method="baseline",
            draft_markdown=draft,
            retrieved_sources=[item.source_id for item in excerpts],
            warnings=warnings,
            model="template",
            latency_ms=elapsed,
        )
    client = make_ollama_client()
    try:
        result = generate_rag(case, documents, client)
    finally:
        client.close()
    warnings.extend(result.warnings)
    if not result.draft_markdown:
        raise HTTPException(status_code=503, detail=warnings[-1] if warnings else "El modelo local no está disponible.")
    return GenerateResponse(
        case_id=result.case_id,
        method="rag",
        draft_markdown=result.draft_markdown,
        retrieved_sources=result.retrieved_source_ids,
        warnings=warnings,
        model=result.model,
        latency_ms=result.latency_ms,
    )


@app.get("/")
def frontend_index():
    """Serve the interface without covering /docs or /api."""
    if INDEX_PATH.is_file():
        return FileResponse(INDEX_PATH)
    return JSONResponse(status_code=404, content={"detail": "La interfaz todavía no está publicada."})
