"""Build cases, gold labels, the split and the diagnostics report.

Run from the backend directory:

    python scripts/build_dataset.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.dataset.builder import (  # noqa: E402
    DatasetValidationError,
    build_dataset,
    write_outputs,
)

DATA_DIR = BACKEND_ROOT / "data" / "synthetic"
REPORT_PATH = BACKEND_ROOT.parent / "reports" / "data_diagnostics.md"


def main() -> int:
    """Validate the reviewed files and write the working dataset."""
    try:
        result = build_dataset(DATA_DIR / "raw", DATA_DIR / "sources")
    except DatasetValidationError as error:
        print(error)
        return 1
    write_outputs(result, DATA_DIR, REPORT_PATH)
    print(
        f"cases={result.manifest['case_count']} "
        f"sources={result.manifest['source_count']} "
        f"development={result.manifest['development_count']} "
        f"test={result.manifest['test_count']} "
        f"warnings={len(result.warnings)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
