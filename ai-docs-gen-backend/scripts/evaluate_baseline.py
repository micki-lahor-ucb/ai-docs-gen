"""Run the deterministic template on the development split only.

    python scripts/evaluate_baseline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.baseline.template_generator import generate_baseline  # noqa: E402
from src.dataset.store import development_ids, load_case_sources, load_cases, load_splits  # noqa: E402
from src.retrieval.tfidf import build_query, retrieve  # noqa: E402

OUTPUT_DIR = BACKEND_ROOT.parent / "reports" / "baseline_dev"


def main() -> int:
    """Write one development draft per case. Test cases are skipped."""
    cases = load_cases()
    test_ids = set(load_splits()["test"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    index = []
    for case_id in development_ids():
        if case_id in test_ids:
            raise RuntimeError(f"Refusing to draft test case {case_id}")
        case = cases[case_id]
        excerpts = retrieve(load_case_sources(case), build_query(case))
        draft = generate_baseline(case, excerpts)
        (OUTPUT_DIR / f"{case_id}.md").write_text(draft, encoding="utf-8")
        index.append(
            {
                "case_id": case_id,
                "retrieved_source_ids": [item.source_id for item in excerpts],
            }
        )
    (OUTPUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"development_drafts={len(index)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
