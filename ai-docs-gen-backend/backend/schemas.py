"""Request and response models for the report API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CASE_ID_PATTERN = r"^SYN-[A-Z]+-\d{4}-\d{3}$"


class SubjectIn(BaseModel):
    """One person supplied with a case."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=200)
    document_type: str = Field(min_length=1, max_length=40)
    document_number: str = Field(min_length=1, max_length=40)
    role: str = Field(min_length=1, max_length=80)


class GenerateRequest(BaseModel):
    """Generation input. Sources always come from the stored case id."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(min_length=1, max_length=40, pattern=CASE_ID_PATTERN)
    method: Literal["baseline", "rag"]
    objective: str | None = Field(default=None, max_length=2000)
    facts: list[str] | None = Field(default=None, max_length=20)
    missing_fields: list[str] | None = Field(default=None, max_length=20)
    contradictions: list[str] | None = Field(default=None, max_length=20)
    legal_status: str | None = Field(default=None, max_length=200)
    subjects: list[SubjectIn] | None = Field(default=None, max_length=10)

    def text_fields_are_bounded(self) -> bool:
        """Reject oversized lines inside the lists."""
        groups = [self.facts or [], self.missing_fields or [], self.contradictions or []]
        return all(len(item) <= 1000 for group in groups for item in group)


class GenerateResponse(BaseModel):
    """Draft returned to the interface."""

    case_id: str
    method: Literal["baseline", "rag"]
    draft_markdown: str
    retrieved_sources: list[str]
    warnings: list[str]
    model: str
    latency_ms: int


class CaseSummary(BaseModel):
    """Short case row for the selector."""

    case_id: str
    department: str
    objective: str


class HealthResponse(BaseModel):
    """Application status without secrets or local paths."""

    status: Literal["ok"]
    ollama: Literal["available", "unavailable", "model_missing"]
    model: str
