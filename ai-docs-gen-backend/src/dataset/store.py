"""Load structured cases and the sources that belong to each case."""

from __future__ import annotations

import json
from pathlib import Path

from src.retrieval.tfidf import SourceDocument

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def load_cases(data_dir: Path = DATA_DIR) -> dict[str, dict]:
    """Load structured cases. Gold labels are not read."""
    rows = [
        json.loads(line)
        for line in (data_dir / "cases.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return {row["case_id"]: row for row in rows}


def load_splits(data_dir: Path = DATA_DIR) -> dict:
    """Load the frozen development and test case ids."""
    return json.loads((data_dir / "splits.json").read_text(encoding="utf-8"))


def development_ids(data_dir: Path = DATA_DIR) -> list[str]:
    """Return development case ids. Test ids are not included."""
    return list(load_splits(data_dir)["development"])


def load_case_sources(case: dict, data_dir: Path = DATA_DIR) -> list[SourceDocument]:
    """Load only the files listed for this case."""
    sources_dir = data_dir / "sources"
    documents = []
    for source_id in case["source_ids"]:
        path = sources_dir / f"{case['case_id']}_{source_id}.md"
        documents.append(SourceDocument(source_id, path.read_text(encoding="utf-8")))
    return documents
