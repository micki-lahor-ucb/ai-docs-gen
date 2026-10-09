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
from src.retrieval.tfidf import SourceDocument, build_query, retrieve  # noqa: E402

DATA_DIR = BACKEND_ROOT / "data" / "synthetic"
OUTPUT_DIR = BACKEND_ROOT.parent / "reports" / "baseline_dev"


def load_cases() -> dict[str, dict]:
    """Load structured cases. Gold labels are not read."""
    rows = [
        json.loads(line)
        for line in (DATA_DIR / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {row["case_id"]: row for row in rows}


def development_ids() -> list[str]:
    """Return the reserved development case ids."""
    splits = json.loads((DATA_DIR / "splits.json").read_text(encoding="utf-8"))
    return list(splits["development"])


def load_case_sources(case: dict) -> list[SourceDocument]:
    """Load only the files listed for this case."""
    sources_dir = DATA_DIR / "sources"
    documents = []
    for source_id in case["source_ids"]:
        path = sources_dir / f"{case['case_id']}_{source_id}.md"
        documents.append(SourceDocument(source_id, path.read_text(encoding="utf-8")))
    return documents


def main() -> int:
    """Write one development draft per case. Test cases are skipped."""
    cases = load_cases()
    test_ids = set(json.loads((DATA_DIR / "splits.json").read_text(encoding="utf-8"))["test"])
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
