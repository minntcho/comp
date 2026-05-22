from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Protocol

from comp.compiler_tool.references import ReferenceOption

RetrievalLens = str

RETRIEVAL_LENSES: tuple[str, ...] = (
    "concept",
    "metric",
    "unit",
    "factor",
    "formula",
    "rubric",
    "rule",
    "memory_skill",
)


@dataclass(frozen=True)
class ReferenceQuery:
    query_id: str
    text: str
    lens: RetrievalLens
    reference_type: str | None = None
    source_artifact_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_lens(self.lens)


@dataclass(frozen=True)
class ReferenceIndexEntry:
    entry_id: str
    reference_id: str
    reference_type: str
    lens: RetrievalLens
    text: str
    reference_db_version: str
    index_version: str
    embedding_model_id: str | None = None
    source: str | None = None
    witness_ids: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_lens(self.lens)


class ReferenceResolver(Protocol):
    def search(
        self,
        query: ReferenceQuery,
        *,
        limit: int = 10,
    ) -> tuple[ReferenceOption, ...]:
        ...


@dataclass(frozen=True)
class EmbeddingResolverStub:
    entries: tuple[ReferenceIndexEntry, ...] = field(default_factory=tuple)

    def search(
        self,
        query: ReferenceQuery,
        *,
        limit: int = 10,
    ) -> tuple[ReferenceOption, ...]:
        scored: list[tuple[float, ReferenceIndexEntry]] = []
        for entry in self.entries:
            if entry.lens != query.lens:
                continue
            if query.reference_type is not None and (
                entry.reference_type != query.reference_type
            ):
                continue

            score = _match_score(query.text, entry.text)
            if score > 0:
                scored.append((score, entry))

        scored.sort(key=lambda item: (-item[0], item[1].reference_id, item[1].entry_id))
        return tuple(
            _candidate_from_entry(query, entry, score)
            for score, entry in scored[:limit]
        )


def _candidate_from_entry(
    query: ReferenceQuery,
    entry: ReferenceIndexEntry,
    score: float,
) -> ReferenceOption:
    return ReferenceOption(
        candidate_id=f"embedding_stub:{query.lens}:{entry.entry_id}",
        reference_id=entry.reference_id,
        reference_type=entry.reference_type,
        retrieval_method=f"embedding_stub:{query.lens}",
        retrieval_score=score,
        source=entry.source,
        witness_ids=entry.witness_ids,
    )


def _validate_lens(lens: str) -> None:
    if lens not in RETRIEVAL_LENSES:
        raise ValueError(f"unknown retrieval lens: {lens}")


def _match_score(query: str, text: str) -> float:
    query_tokens = set(_tokens(query))
    if not query_tokens:
        return 0.0

    entry_tokens = set(_tokens(text))
    overlap = query_tokens & entry_tokens
    if not overlap:
        return 0.0
    return round(len(overlap) / len(query_tokens), 6)


def _tokens(value: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[^a-z0-9]+", value.lower()) if token)


__all__ = [
    "RETRIEVAL_LENSES",
    "RetrievalLens",
    "ReferenceQuery",
    "ReferenceIndexEntry",
    "ReferenceResolver",
    "EmbeddingResolverStub",
]
