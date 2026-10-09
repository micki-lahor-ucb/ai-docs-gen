"""Copy test drafts without method, model or latency, then shuffle them."""

from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

RAW_DIR = BACKEND_ROOT.parent / "reports" / "test_raw"
BLIND_DIR = BACKEND_ROOT.parent / "reports" / "blind_review"
SEED = 42


def main() -> int:
    """Write opaque drafts and an empty rubric. The key stays beside the raw files."""
    frozen = json.loads((RAW_DIR / "frozen.json").read_text(encoding="utf-8"))
    items = []
    for row in frozen["cases"]:
        case_id = row["case_id"]
        for method in ("baseline", "rag"):
            text = (RAW_DIR / f"{case_id}_{method}.md").read_text(encoding="utf-8")
            items.append({"case_id": case_id, "method": method, "text": text})
    random.Random(SEED).shuffle(items)
    BLIND_DIR.mkdir(parents=True, exist_ok=True)
    key = []
    rubric_path = BLIND_DIR / "rubric.csv"
    with rubric_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "blind_id",
                "fidelity",
                "no_invention",
                "verifiable_sources",
                "missing_handled",
                "completeness",
                "pertinence",
                "format",
                "notes",
            ],
        )
        writer.writeheader()
        for index, item in enumerate(items, start=1):
            blind_id = f"D{index:02d}"
            (BLIND_DIR / f"{blind_id}.md").write_text(item["text"], encoding="utf-8")
            writer.writerow({name: blind_id if name == "blind_id" else "" for name in writer.fieldnames})
            key.append({"blind_id": blind_id, "case_id": item["case_id"], "method": item["method"]})
    (RAW_DIR / "blind_key.json").write_text(
        json.dumps(key, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"blind_drafts={len(items)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
