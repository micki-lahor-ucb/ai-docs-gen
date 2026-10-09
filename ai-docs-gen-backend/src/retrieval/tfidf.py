"""TF-IDF retrieval fitted only on the sources of one case."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

TOP_K = 3


@dataclass(frozen=True)
class SourceDocument:
    """One source that belongs to a single case."""

    source_id: str
    text: str


@dataclass(frozen=True)
class RetrievedSource:
    """A source selected for the draft, with its similarity score."""

    source_id: str
    text: str
    score: float


def build_query(case: dict) -> str:
    """Build the query from the objective and the structured facts only."""
    facts = [str(fact) for fact in case.get("facts") or []]
    return " ".join([str(case.get("objective") or ""), *facts]).strip()


def retrieve(documents: list[SourceDocument], query: str, top_k: int = TOP_K) -> list[RetrievedSource]:
    """Return at most top_k sources from this case.

    The vectorizer is fitted on these documents alone. Relevance labels are
    not an input.
    """
    if top_k < 1:
        raise ValueError("top_k must be at least 1")
    if not documents:
        return []

    ordered = sorted(documents, key=lambda document: document.source_id)
    if not query.strip():
        return [
            RetrievedSource(document.source_id, document.text, 0.0)
            for document in ordered[:top_k]
        ]

    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform([document.text for document in ordered])
    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, matrix).ravel()
    if not np.isfinite(scores).any() or float(np.max(scores)) == 0.0:
        return [
            RetrievedSource(document.source_id, document.text, 0.0)
            for document in ordered[:top_k]
        ]

    ranking = sorted(
        range(len(ordered)),
        key=lambda index: (-float(scores[index]), ordered[index].source_id),
    )
    return [
        RetrievedSource(ordered[index].source_id, ordered[index].text, float(scores[index]))
        for index in ranking[:top_k]
    ]
