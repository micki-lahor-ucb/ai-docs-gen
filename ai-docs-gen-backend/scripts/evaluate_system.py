"""Aggregate the frozen test. Human labels are never invented."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.dataset.builder import difficulty_tags  # noqa: E402
from src.dataset.store import DATA_DIR, load_cases  # noqa: E402
from src.evaluation.metrics import (  # noqa: E402
    critical_passed,
    is_accepted,
    recall_at_k,
    reference_text,
    rouge_l,
    wilson_interval,
)

ROOT = BACKEND_ROOT.parent
RAW_DIR = ROOT / "reports" / "test_raw"
BLIND_DIR = ROOT / "reports" / "blind_review"
REPORT_PATH = ROOT / "reports" / "results.md"


def load_rows() -> list[dict]:
    """Join the rubric to the hidden key. Blank scores stay blank."""
    key = {item["blind_id"]: item for item in json.loads((RAW_DIR / "blind_key.json").read_text(encoding="utf-8"))}
    with (BLIND_DIR / "rubric.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    joined = []
    for row in rows:
        meta = key[row["blind_id"]]
        joined.append({**row, "case_id": meta["case_id"], "method": meta["method"]})
    return joined


def main() -> int:
    """Write the results report. Missing labels stop the acceptance rates."""
    frozen = json.loads((RAW_DIR / "frozen.json").read_text(encoding="utf-8"))
    gold = {
        json.loads(line)["case_id"]: json.loads(line)
        for line in (DATA_DIR / "gold_labels.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    cases = load_cases()
    rows = load_rows()
    baseline_ids = {row["case_id"] for row in rows if row["method"] == "baseline"}
    rag_ids = {row["case_id"] for row in rows if row["method"] == "rag"}
    if baseline_ids != rag_ids:
        print("Baseline y RAG no tienen los mismos case_id.")
        return 1
    missing = [
        row["blind_id"]
        for row in rows
        if is_accepted(row) is None or any(row.get(name, "").strip() == "" for name in ("pertinence", "format"))
    ]
    retrieved = {item["case_id"]: item for item in frozen["cases"]}
    recalls = [
        recall_at_k(retrieved[case_id]["retrieved_source_ids"], gold[case_id]["relevant_source_ids"])
        for case_id in sorted(baseline_ids)
    ]
    recall_mean = sum(value for value in recalls if value is not None) / len(recalls)
    lines = [
        "# Resultados de la prueba",
        "",
        f"Commit congelado: `{frozen['frozen_commit']}`.",
        "El intervalo de Wilson, cuando se calcule, describe incertidumbre y no declara un ganador.",
        "ROUGE-L es exploratorio y no mide veracidad.",
        "",
        f"Recall@3 de la recuperación compartida: {recall_mean:.3f} sobre {len(recalls)} casos.",
        "",
    ]
    if missing:
        lines.append("Faltan etiquetas humanas. No se calcula la tasa de aceptación y no se asume que un borrador pasó.")
        lines.append("")
        lines.append("Identificadores sin ficha completa: " + ", ".join(missing))
        lines.append("")
    else:
        lines.extend(render_table(rows, retrieved, gold, cases))
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"missing_labels={len(missing)} recall_at_3={recall_mean:.3f}")
    return 0


def render_table(rows: list[dict], retrieved: dict, gold: dict, cases: dict) -> list[str]:
    """Build the comparison from completed human labels."""
    lines = [
        "| Métrica | Plantilla | RAG |",
        "|---|---:|---:|",
    ]
    summary = {}
    for method in ("baseline", "rag"):
        subset = [row for row in rows if row["method"] == method]
        accepted_count = sum(bool(is_accepted(row)) for row in subset)
        critical_count = sum(bool(critical_passed(row)) for row in subset)
        critical_errors = sum(
            sum(
                1
                for name in ("fidelity", "no_invention", "verifiable_sources", "missing_handled")
                if str(row[name]).strip().lower() in {"fail", "no", "reprobado", "false", "0"}
            )
            for row in subset
        )
        low, high = wilson_interval(accepted_count, len(subset))
        latencies = [retrieved[row["case_id"]]["rag_latency_ms"] for row in subset]
        rouge_scores = []
        for row in subset:
            draft = (RAW_DIR / f"{row['case_id']}_{method}.md").read_text(encoding="utf-8")
            score = rouge_l(draft, reference_text(gold[row["case_id"]]))
            if score is not None:
                rouge_scores.append(score)
        summary[method] = {
            "accepted": f"{accepted_count}/{len(subset)}",
            "wilson": f"{low:.3f}–{high:.3f}",
            "critical": f"{critical_count}/{len(subset)}",
            "critical_errors": str(critical_errors),
            "pertinence": rate(subset, "pertinence"),
            "format": rate(subset, "format"),
            "rouge": f"{statistics.fmean(rouge_scores):.3f}" if rouge_scores else "—",
            "latency": f"{statistics.median(latencies) / 1000:.1f} s" if method == "rag" else "0 s",
        }
    recalls = [
        recall_at_k(retrieved[case_id]["retrieved_source_ids"], gold[case_id]["relevant_source_ids"])
        for case_id in retrieved
    ]
    recall_text = f"{statistics.fmean(recalls):.3f}"
    pairs = [
        ("Borradores aceptables", "accepted"),
        ("Tasa de aceptación (Wilson 95 %)", "wilson"),
        ("Cuatro críticos aprobados", "critical"),
        ("Errores críticos", "critical_errors"),
        ("Pertinencia", "pertinence"),
        ("Formato", "format"),
        ("ROUGE-L exploratorio", "rouge"),
        ("Latencia mediana", "latency"),
    ]
    for label, key in pairs:
        lines.append(f"| {label} | {summary['baseline'][key]} | {summary['rag'][key]} |")
    lines.append(f"| Recall@3 de la recuperación compartida | {recall_text} | {recall_text} |")
    lines.extend(["", "## Corte por tipo de caso", ""])
    for case_id in sorted(retrieved):
        tags = ", ".join(difficulty_tags(cases[case_id], DATA_DIR / "sources"))
        lines.append(f"- {case_id}: {tags}")
    lines.append("")
    return lines


def rate(rows: list[dict], name: str) -> str:
    """Format a complementary pass rate."""
    passed = sum(1 for row in rows if str(row[name]).strip().lower() in {"pass", "si", "sí", "aprobado", "true", "1"})
    return f"{passed}/{len(rows)}"


if __name__ == "__main__":
    raise SystemExit(main())
