"""Build the working dataset from reviewed case files and source documents.

The seed fixes the split only. Source prose is read from versioned files and
is not regenerated.
"""

from __future__ import annotations

import json
import random
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

SEED = 42
DEVELOPMENT_COUNT = 16
SYNTHETIC_MARKER = "DOCUMENTO SINTÉTICO PARA EVALUACIÓN ACADÉMICA"
REQUIRED_CASE_FIELDS = (
    "case_id",
    "cud",
    "department",
    "report_date",
    "subjects",
    "legal_status",
    "objective",
    "facts",
    "missing_fields",
    "contradictions",
    "source_ids",
    "evaluation_key",
)
REQUIRED_SUBJECT_FIELDS = ("name", "document_type", "document_number", "role")
ADVERSARIAL_PATTERNS = (
    "a partir de ahora",
    "a partir de este punto",
    "ignora",
    "instrucciones previas",
    "viñetas",
    "letras mayúsculas",
    "mayúsculas",
)
STOPWORDS = {
    "el",
    "la",
    "los",
    "las",
    "de",
    "del",
    "que",
    "en",
    "un",
    "una",
    "por",
    "con",
    "para",
    "su",
    "sus",
    "al",
    "lo",
    "se",
    "es",
    "son",
    "fue",
    "y",
    "o",
    "a",
    "como",
    "durante",
    "este",
    "esta",
    "ese",
    "esa",
}


class DatasetValidationError(Exception):
    """Raised when reviewed files cannot form a valid dataset."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("\n".join(errors))


@dataclass
class BuildResult:
    """Artifacts produced by one deterministic build."""

    cases: list[dict]
    gold_labels: list[dict]
    splits: dict
    manifest: dict
    diagnostics: str
    warnings: list[str] = field(default_factory=list)


def normalize_text(value: str) -> str:
    """Lowercase text and drop accents and punctuation."""
    decomposed = unicodedata.normalize("NFD", value.lower())
    without_accents = "".join(
        character for character in decomposed if unicodedata.category(character) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def content_tokens(value: str) -> list[str]:
    """Return informative tokens used to check whether a fact is supported."""
    return [
        token
        for token in normalize_text(value).split()
        if len(token) >= 4 and token not in STOPWORDS
    ]


def fact_supported_by_text(fact: str, document: str, minimum_ratio: float = 0.7) -> bool:
    """Return whether enough informative tokens of a fact appear in a document."""
    tokens = content_tokens(fact)
    if not tokens:
        return normalize_text(fact) in normalize_text(document)
    document_tokens = set(normalize_text(document).split())
    matched = sum(1 for token in tokens if token in document_tokens)
    return matched / len(tokens) >= minimum_ratio


def fact_in_structured_fields(fact: str, case: dict) -> bool:
    """Return whether a source-only fact was copied into the structured case."""
    parts = [case.get("objective") or ""]
    for key in ("facts", "missing_fields", "contradictions"):
        parts.extend(str(item) for item in case.get(key) or [])
    if case.get("legal_status"):
        parts.append(str(case["legal_status"]))
    return normalize_text(fact) in normalize_text(" ".join(parts))


def is_adversarial(document: str) -> bool:
    """Detect a source paragraph that tries to change drafting rules."""
    normalized = normalize_text(document)
    return any(normalize_text(pattern) in normalized for pattern in ADVERSARIAL_PATTERNS)


def load_batches(raw_dir: Path) -> list[dict]:
    """Load cases from reviewed batch files, in filename order."""
    paths = sorted(raw_dir.glob("batch_*.json"))
    if not paths:
        raise DatasetValidationError([f"No batch files found in {raw_dir}"])
    cases: list[dict] = []
    for path in paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        batch_cases = payload.get("cases")
        if not isinstance(batch_cases, list):
            raise DatasetValidationError([f"{path.name} does not contain a cases list"])
        cases.extend(batch_cases)
    return cases


def read_source(sources_dir: Path, case_id: str, source_id: str) -> str:
    """Read one source document."""
    path = sources_dir / f"{case_id}_{source_id}.md"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path.read_text(encoding="utf-8")


def validate_cases(cases: list[dict], sources_dir: Path) -> tuple[list[str], list[str]]:
    """Return hard errors and warnings. Does not rewrite case content."""
    errors: list[str] = []
    warnings: list[str] = []
    seen_cases: set[str] = set()
    seen_sources: set[str] = set()
    referenced_files: set[str] = set()

    for case in cases:
        case_id = str(case.get("case_id") or "")
        for required in REQUIRED_CASE_FIELDS:
            if required not in case:
                errors.append(f"{case_id or '<missing>'}: missing field {required}")
        if not case_id:
            continue
        if case_id in seen_cases:
            errors.append(f"Duplicate case_id: {case_id}")
        seen_cases.add(case_id)

        subjects = case.get("subjects") or []
        if not subjects:
            errors.append(f"{case_id}: subjects is empty")
        for subject in subjects:
            for required in REQUIRED_SUBJECT_FIELDS:
                if required not in subject:
                    errors.append(f"{case_id}: subject missing {required}")

        source_ids = case.get("source_ids") or []
        if len(source_ids) not in (5, 6):
            errors.append(f"{case_id}: expected 5 or 6 sources, found {len(source_ids)}")
        if len(source_ids) != len(set(source_ids)):
            errors.append(f"{case_id}: duplicated source_ids inside the case")

        evaluation = case.get("evaluation_key") or {}
        relevant = evaluation.get("relevant_source_ids") or []
        if len(relevant) < 1:
            errors.append(f"{case_id}: relevant_source_ids is empty")
        for source_id in relevant:
            if source_id not in source_ids:
                errors.append(f"{case_id}: relevant source {source_id} is not in source_ids")

        exclusive = evaluation.get("source_only_facts") or []
        if len(exclusive) < 2:
            errors.append(f"{case_id}: expected at least two source-only facts")

        for source_id in source_ids:
            if source_id in seen_sources:
                errors.append(f"Duplicate source_id: {source_id}")
            seen_sources.add(source_id)
            filename = f"{case_id}_{source_id}.md"
            referenced_files.add(filename)
            try:
                document = read_source(sources_dir, case_id, source_id)
            except FileNotFoundError:
                errors.append(f"{case_id}: missing source file {filename}")
                continue
            if SYNTHETIC_MARKER not in document:
                errors.append(f"{filename}: missing synthetic label")
            if f"case_id: {case_id}" not in document or f"source_id: {source_id}" not in document:
                errors.append(f"{filename}: header does not match the filename")

        for item in exclusive:
            fact = item.get("text") or ""
            source_id = item.get("source_id") or ""
            if source_id not in source_ids:
                errors.append(f"{case_id}: fact {item.get('fact_id')} cites unknown {source_id}")
                continue
            if fact_in_structured_fields(fact, case):
                errors.append(f"{case_id}: source-only fact appears in structured fields: {fact}")
            try:
                document = read_source(sources_dir, case_id, source_id)
            except FileNotFoundError:
                continue
            if not fact_supported_by_text(fact, document):
                warnings.append(
                    f"{case_id}: fact wording is not supported by {source_id}: {fact}"
                )

    for path in sources_dir.glob("*.md"):
        if path.name not in referenced_files:
            warnings.append(f"Unreferenced source file: {path.name}")

    return errors, warnings


def assign_split(case_ids: list[str], seed: int = SEED) -> dict:
    """Split whole cases into development and test. The same seed is stable."""
    ordered = sorted(case_ids)
    random.Random(seed).shuffle(ordered)
    if len(ordered) < DEVELOPMENT_COUNT + 1:
        raise DatasetValidationError(
            [f"Need more than {DEVELOPMENT_COUNT} cases to reserve a test split"]
        )
    development = ordered[:DEVELOPMENT_COUNT]
    test = ordered[DEVELOPMENT_COUNT:]
    return {
        "seed": seed,
        "development": development,
        "test": test,
    }


def case_record(case: dict) -> dict:
    """Return the structured case without the evaluation key."""
    record = {key: case[key] for key in REQUIRED_CASE_FIELDS if key != "evaluation_key"}
    return record


def gold_record(case: dict) -> dict:
    """Return the evaluation key for one case."""
    evaluation = case["evaluation_key"]
    return {
        "case_id": case["case_id"],
        "relevant_source_ids": evaluation.get("relevant_source_ids") or [],
        "required_facts": evaluation.get("required_facts") or [],
        "source_only_facts": evaluation.get("source_only_facts") or [],
    }


def approximate_word_count(sources_dir: Path, cases: list[dict]) -> int:
    """Count words in the source documents referenced by the cases."""
    total = 0
    for case in cases:
        for source_id in case["source_ids"]:
            document = read_source(sources_dir, case["case_id"], source_id)
            total += len(re.findall(r"\S+", document))
    return total


def difficulty_tags(case: dict, sources_dir: Path) -> list[str]:
    """Label a case from its fields and source text. A case may have several tags."""
    tags: list[str] = []
    if case.get("contradictions"):
        tags.append("contradiccion")
    if case.get("missing_fields"):
        tags.append("faltantes")
    documents = [
        read_source(sources_dir, case["case_id"], source_id) for source_id in case["source_ids"]
    ]
    if any(is_adversarial(document) for document in documents):
        tags.append("adversarial")
    if not tags:
        tags.append("suficiente")
    return tags


def render_diagnostics(
    cases: list[dict],
    splits: dict,
    sources_dir: Path,
    warnings: list[str],
    word_count: int,
) -> str:
    """Write the Spanish diagnostics report from measured counts."""
    by_id = {case["case_id"]: case for case in cases}
    lines = [
        "# Diagnóstico del dataset",
        "",
        "Textos sintéticos elaborados para este prototipo y revisados por el autor.",
        "La semilla 42 fija la partición. No regenera los textos fuente, porque esos archivos ya están versionados.",
        "",
        "## Conteos",
        "",
        f"- Casos: {len(cases)}",
        f"- Fuentes: {sum(len(case['source_ids']) for case in cases)}",
        f"- Palabras aproximadas en las fuentes: {word_count}",
        f"- Desarrollo: {len(splits['development'])}",
        f"- Prueba: {len(splits['test'])}",
        "",
        "## Dificultad",
        "",
        "| Caso | Partición | Etiquetas | Fuentes | Pertinentes | Distractores | Hechos exclusivos |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for case in sorted(cases, key=lambda item: item["case_id"]):
        partition = "prueba" if case["case_id"] in splits["test"] else "desarrollo"
        relevant = len(case["evaluation_key"]["relevant_source_ids"])
        total_sources = len(case["source_ids"])
        exclusive = len(case["evaluation_key"]["source_only_facts"])
        tags = ", ".join(difficulty_tags(case, sources_dir))
        lines.append(
            f"| {case['case_id']} | {partition} | {tags} | {total_sources} | {relevant} | {total_sources - relevant} | {exclusive} |"
        )

    test_tags = [difficulty_tags(by_id[case_id], sources_dir) for case_id in splits["test"]]
    dev_tags = [difficulty_tags(by_id[case_id], sources_dir) for case_id in splits["development"]]
    lines.extend(
        [
            "",
            "## Partición",
            "",
            f"- Desarrollo con contradicción: {sum('contradiccion' in tags for tags in dev_tags)}",
            f"- Desarrollo con faltantes: {sum('faltantes' in tags for tags in dev_tags)}",
            f"- Desarrollo con texto que intenta cambiar la redacción: {sum('adversarial' in tags for tags in dev_tags)}",
            f"- Prueba con contradicción: {sum('contradiccion' in tags for tags in test_tags)}",
            f"- Prueba con faltantes: {sum('faltantes' in tags for tags in test_tags)}",
            f"- Prueba con texto que intenta cambiar la redacción: {sum('adversarial' in tags for tags in test_tags)}",
            "",
            "## Avisos",
            "",
        ]
    )
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- Ninguno.")
    lines.append("")
    return "\n".join(lines)


def build_manifest(cases: list[dict], splits: dict, word_count: int) -> dict:
    """Describe origin, seed scope and limitations without regenerating prose."""
    return {
        "seed": SEED,
        "case_count": len(cases),
        "source_count": sum(len(case["source_ids"]) for case in cases),
        "approximate_source_words": word_count,
        "development_count": len(splits["development"]),
        "test_count": len(splits["test"]),
        "origin": "Textos sintéticos elaborados para este prototipo y revisados por el autor.",
        "seed_scope": (
            "SEED=42 fija la validación de la construcción y la partición por caso. "
            "No regenera los textos fuente, porque esos archivos ya están versionados."
        ),
        "limitations": [
            "No representan expedientes reales.",
            "El volumen es reducido y el resultado sobre la prueba es exploratorio.",
            "Una sola persona revisó los textos.",
            "La semilla no vuelve a redactar las fuentes.",
        ],
    }


def build_dataset(raw_dir: Path, sources_dir: Path) -> BuildResult:
    """Validate reviewed files and return dataset artifacts."""
    cases = load_batches(raw_dir)
    errors, warnings = validate_cases(cases, sources_dir)
    if errors:
        raise DatasetValidationError(errors)
    splits = assign_split([case["case_id"] for case in cases])
    ordered = sorted(cases, key=lambda item: item["case_id"])
    word_count = approximate_word_count(sources_dir, ordered)
    return BuildResult(
        cases=[case_record(case) for case in ordered],
        gold_labels=[gold_record(case) for case in ordered],
        splits=splits,
        manifest=build_manifest(ordered, splits, word_count),
        diagnostics=render_diagnostics(ordered, splits, sources_dir, warnings, word_count),
        warnings=warnings,
    )


def write_json(path: Path, payload: dict) -> None:
    """Write JSON with stable key order."""
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    """Write one JSON object per line."""
    lines = [json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_outputs(result: BuildResult, data_dir: Path, report_path: Path) -> None:
    """Persist the working dataset and the diagnostics report."""
    data_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(data_dir / "cases.jsonl", result.cases)
    write_jsonl(data_dir / "gold_labels.jsonl", result.gold_labels)
    write_json(data_dir / "splits.json", result.splits)
    write_json(data_dir / "manifest.json", result.manifest)
    report_path.write_text(result.diagnostics, encoding="utf-8")
