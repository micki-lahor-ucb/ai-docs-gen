"""Fill a fixed Spanish template. Excerpts are pasted, not rewritten."""

from __future__ import annotations

from src.retrieval.tfidf import RetrievedSource

PENDING = "[PENDIENTE: información no proporcionada]"


def excerpt_body(document: str) -> str:
    """Drop the file header and return the source text unchanged."""
    lines = document.splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.startswith("- source_id:"):
            start = index + 1
            break
    return "\n".join(lines[start:]).strip()


def _value(value: object) -> str:
    if value is None or str(value).strip() == "":
        return PENDING
    return str(value).strip()


def _bullet_list(items: list[str]) -> str:
    if not items:
        return PENDING
    return "\n".join(f"- {item}" for item in items)


def _subjects(subjects: list[dict]) -> str:
    if not subjects:
        return PENDING
    lines = []
    for subject in subjects:
        lines.append(
            "- Nombre: {name}; documento: {document_type} {document_number}; rol: {role}".format(
                name=_value(subject.get("name")),
                document_type=_value(subject.get("document_type")),
                document_number=_value(subject.get("document_number")),
                role=_value(subject.get("role")),
            )
        )
    return "\n".join(lines)


def _contradictions(items: list[str]) -> str:
    if not items:
        return "No se registraron contradicciones en los datos del caso."
    return _bullet_list(items)


def _missing(items: list[str]) -> str:
    if not items:
        return "No se registraron campos faltantes en los datos del caso."
    return _bullet_list([_value(item) for item in items])


def generate_baseline(case: dict, excerpts: list[RetrievedSource]) -> str:
    """Render one draft from structured fields and the retrieved excerpts."""
    facts = [str(fact) for fact in case.get("facts") or []]
    sections = [
        "# Informe breve de antecedentes",
        "",
        "Borrador producido con una plantilla determinista. No es un documento oficial y requiere revisión humana.",
        "",
        "## Identificación del caso",
        "",
        f"- Identificador: {_value(case.get('case_id'))}",
        f"- CUD: {_value(case.get('cud'))}",
        f"- Departamento: {_value(case.get('department'))}",
        f"- Fecha de informe: {_value(case.get('report_date'))}",
        f"- Situación jurídica: {_value(case.get('legal_status'))}",
        "",
        "## Sujetos procesales",
        "",
        _subjects(case.get("subjects") or []),
        "",
        "## Objetivo",
        "",
        _value(case.get("objective")),
        "",
        "## Antecedentes conocidos",
        "",
        _bullet_list(facts),
        "",
        "## Contradicciones registradas",
        "",
        _contradictions([str(item) for item in case.get("contradictions") or []]),
        "",
        "## Datos faltantes",
        "",
        _missing([str(item) for item in case.get("missing_fields") or []]),
        "",
        "## Documentación revisada",
        "",
    ]
    if not excerpts:
        sections.append(PENDING)
    for excerpt in excerpts:
        sections.extend(
            [
                f"### Fuente: {excerpt.source_id}",
                "",
                excerpt_body(excerpt.text),
                "",
            ]
        )
    return "\n".join(sections).rstrip() + "\n"
