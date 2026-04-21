from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Protocol

from comp.judgment.core import Fact, FactTag, JudgmentState, SubjectKind


class TransferEmitter(Protocol):
    def __call__(self, state: JudgmentState, triggered: frozenset[Fact]) -> Iterable[Fact]:
        ...


@dataclass(frozen=True)
class TransferRule:
    rule_id: str
    subscribe_tags: tuple[FactTag, ...]
    emit: TransferEmitter
    match_kind: SubjectKind | None = None


@dataclass(frozen=True)
class BundleSpec:
    bundle_id: str
    candidate_key: str
    required_for_commit: bool = True


@dataclass(frozen=True)
class CommitSpec:
    commit_id: str
    required_bundles: tuple[str, ...] = ()
    blocking_hazards: tuple[str, ...] = ()
    min_provenance_edges: int = 0
    require_fresh: bool = True


@dataclass(frozen=True)
class ProjectionSpec:
    projection_id: str
    output_fields: tuple[str, ...]


@dataclass(frozen=True)
class CompiledJudgmentProgram:
    transfers: tuple[TransferRule, ...] = field(default_factory=tuple)
    bundles: tuple[BundleSpec, ...] = field(default_factory=tuple)
    commits: tuple[CommitSpec, ...] = field(default_factory=tuple)
    projections: tuple[ProjectionSpec, ...] = field(default_factory=tuple)


__all__ = [
    "TransferEmitter",
    "TransferRule",
    "BundleSpec",
    "CommitSpec",
    "ProjectionSpec",
    "CompiledJudgmentProgram",
]
