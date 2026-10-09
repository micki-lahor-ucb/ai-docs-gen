"""Generate the official test drafts once. Does not score them."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.baseline.template_generator import generate_baseline  # noqa: E402
from src.dataset.store import load_case_sources, load_cases, load_splits  # noqa: E402
from src.generation.generator import generate_rag  # noqa: E402
from src.generation.ollama_client import OllamaClient  # noqa: E402
from src.retrieval.tfidf import build_query, retrieve  # noqa: E402

OUTPUT_DIR = BACKEND_ROOT.parent / "reports" / "test_raw"
FROZEN_COMMIT = "f4ca646"


def main() -> int:
    """Write baseline and model drafts for the frozen test split."""
    marker = OUTPUT_DIR / "frozen.json"
    if marker.exists():
        print("La prueba ya fue generada. No se vuelve a ejecutar.")
        return 1
    cases = load_cases()
    test_ids = list(load_splits()["test"])
    development_ids = set(load_splits()["development"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OllamaClient()
    rows = []
    try:
        for case_id in test_ids:
            if case_id in development_ids:
                raise RuntimeError(f"El identificador {case_id} está en desarrollo")
            case = cases[case_id]
            documents = load_case_sources(case)
            excerpts = retrieve(documents, build_query(case))
            baseline = generate_baseline(case, excerpts)
            (OUTPUT_DIR / f"{case_id}_baseline.md").write_text(baseline, encoding="utf-8")
            rag = generate_rag(case, documents, client)
            (OUTPUT_DIR / f"{case_id}_rag.md").write_text(rag.draft_markdown, encoding="utf-8")
            rows.append(
                {
                    "case_id": case_id,
                    "retrieved_source_ids": [item.source_id for item in excerpts],
                    "baseline_latency_ms": 0,
                    "rag_model": rag.model,
                    "rag_latency_ms": rag.latency_ms,
                    "rag_warnings": rag.warnings,
                }
            )
            print(f"{case_id} model={rag.model or '-'} latency_ms={rag.latency_ms}")
    finally:
        client.close()
    payload = {"frozen_commit": FROZEN_COMMIT, "cases": rows}
    marker.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"test_cases={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
