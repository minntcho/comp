from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Literal

SubjectKind = Literal[
    "raw",
    "claim",
    "bundle",
    "draft",
    "public_row",
    "rule",
    "policy",
    "projection",
]

FactTag = Literal[
    "proposed",
    "evidence",
    "hazard_open",
    "hazard_discharge",
    "prov_edge",
]


@dataclass(frozen=True, slots=True)
class SubjectRef:
    kind: SubjectKind
    id: str


@dataclass(frozen=True, slots=True)
class Fact:
    tag: FactTag
    subject: SubjectRef
    key: str
    value: Any
    witness: str | None = None
    weight: float | None = None
    meta: tuple[tuple[str, Any], ...] = ()


@dataclass
class JudgmentState:
    facts: set[Fact] = field(default_factory=set)
    subject_versions: dict[SubjectRef, int] = field(default_factory=dict)

    def add_facts(self, new_facts: Iterable[Fact]) -> set[Fact]:
        incoming = set(new_facts)
        delta = incoming - self.facts
        if not delta:
            return set()

        self.facts |= delta
        for subject in {fact.subject for fact in delta}:
            self.subject_versions[subject] = self.subject_versions.get(subject, 0) + 1
        return delta

    def version_of(self, subject: SubjectRef) -> int:
        return self.subject_versions.get(subject, 0)

    def facts_for(self, subject: SubjectRef) -> set[Fact]:
        return {fact for fact in self.facts if fact.subject == subject}

    def facts_by_tag(self, tag: FactTag) -> set[Fact]:
        return {fact for fact in self.facts if fact.tag == tag}

    def active_hazard_ids(self, subject: SubjectRef) -> set[Any]:
        opened = {
            fact.value
            for fact in self.facts
            if fact.tag == "hazard_open" and fact.subject == subject
        }
        discharged = {
            fact.value
            for fact in self.facts
            if fact.tag == "hazard_discharge" and fact.subject == subject
        }
        return opened - discharged


__all__ = [
    "SubjectKind",
    "FactTag",
    "SubjectRef",
    "Fact",
    "JudgmentState",
]
