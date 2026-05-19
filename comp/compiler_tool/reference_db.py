from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from comp.compiler_tool.references import ReferenceCandidate


class ReferenceLookupError(KeyError):
    """Raised when a requested canonical reference row is absent."""


@dataclass(frozen=True)
class ReferenceRecord:
    reference_id: str
    reference_type: str
    labels: tuple[str, ...] = field(default_factory=tuple)
    aliases: tuple[str, ...] = field(default_factory=tuple)
    description: str = ""
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    source: str | None = None
    witness_ids: tuple[str, ...] = field(default_factory=tuple)

    def attribute(self, name: str, default: Any = None) -> Any:
        for key, value in self.attributes:
            if key == name:
                return value
        return default

    def to_candidate(
        self,
        *,
        candidate_id: str,
        retrieval_method: str,
        retrieval_score: float | None = None,
    ) -> ReferenceCandidate:
        return ReferenceCandidate(
            candidate_id=candidate_id,
            reference_id=self.reference_id,
            reference_type=self.reference_type,
            retrieval_method=retrieval_method,
            retrieval_score=retrieval_score,
            source=self.source,
            witness_ids=self.witness_ids,
        )


@dataclass(frozen=True)
class ReferenceCatalog:
    records: tuple[ReferenceRecord, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for record in self.records:
            if record.reference_id in seen:
                raise ValueError(f"duplicate reference id: {record.reference_id}")
            seen.add(record.reference_id)

    def get(self, reference_id: str) -> ReferenceRecord:
        for record in self.records:
            if record.reference_id == reference_id:
                return record
        raise ReferenceLookupError(f"unknown reference id: {reference_id}")

    def search(
        self,
        query: str,
        *,
        reference_type: str | None = None,
        limit: int = 10,
        retrieval_method: str = "keyword",
    ) -> tuple[ReferenceCandidate, ...]:
        scored: list[tuple[float, ReferenceRecord]] = []
        for record in self.records:
            if reference_type is not None and record.reference_type != reference_type:
                continue

            score = _match_score(query, record)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda item: (-item[0], item[1].reference_id))
        return tuple(
            record.to_candidate(
                candidate_id=f"{retrieval_method}:{record.reference_id}",
                retrieval_method=retrieval_method,
                retrieval_score=score,
            )
            for score, record in scored[:limit]
        )


def _match_score(query: str, record: ReferenceRecord) -> float:
    normalized_query = _normalize_text(query)
    names = (*record.labels, *record.aliases)
    if any(_normalize_text(name) == normalized_query for name in names):
        return 1.0

    query_tokens = set(_tokens(query))
    if not query_tokens:
        return 0.0

    record_tokens = set(
        _tokens(" ".join((*record.labels, *record.aliases, record.description)))
    )
    overlap = query_tokens & record_tokens
    if not overlap:
        return 0.0
    return round(len(overlap) / len(query_tokens), 6)


def _normalize_text(value: str) -> str:
    return " ".join(_tokens(value))


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[^a-z0-9]+", value.lower()) if token)


__all__ = [
    "ReferenceLookupError",
    "ReferenceRecord",
    "ReferenceCatalog",
]
