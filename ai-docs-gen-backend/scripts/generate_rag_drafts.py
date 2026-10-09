"""Generate local-model drafts for the development split only.

    python scripts/generate_rag_drafts.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.dataset.store import development_ids, load_case_sources, load_cases, load_splits  # noqa: E402
from src.generation.generator import generate_rag  # noqa: E402
from src.generation.ollama_client import OllamaClient  # noqa: E402

OUTPUT_DIR = BACKEND_ROOT.parent / "reports" / "rag_dev"


def main() -> int:
    """Write one development draft per case. Test cases are skipped."""
    cases = load_cases()
    test_ids = set(load_splits()["test"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    client = OllamaClient()
    index = []
    try:
        for case_id in development_ids():
            if case_id in test_ids:
                raise RuntimeError(f"Refusing to draft test case {case_id}")
            case = cases[case_id]
            result = generate_rag(case, load_case_sources(case), client)
            (OUTPUT_DIR / f"{case_id}.md").write_text(result.draft_markdown, encoding="utf-8")
            index.append(
                {
                    "case_id": result.case_id,
                    "model": result.model,
                    "latency_ms": result.latency_ms,
                    "retrieved_source_ids": result.retrieved_source_ids,
                    "warnings": result.warnings,
                }
            )
            print(f"{case_id} model={result.model or '-'} latency_ms={result.latency_ms} warnings={len(result.warnings)}")
    finally:
        client.close()
    (OUTPUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"development_drafts={len(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
