from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional, Sequence

from comp.dsl.spec_nodes import ProgramSpec


@dataclass
class LexCandidate:
    value: Any
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ScopeFrame:
    level: str        # document / section / table / row / cell
    ref_id: str       # e.g. "doc:1", "table:2", "row:8"


ScopePath = tuple[ScopeFrame, ...]


@dataclass
class ContextEntry:
    context_id: str
    role_name: str
    value: Any

    scope_path: ScopePath
    ttl: str                      # document / section / table / column / row / cell_only
    precedence: int = 0
    operation: str = "override"  # override / refine / conflict / mask

    source_fragment_id: Optional[str] = None
    source_claim_id: Optional[str] = None
    column_key: Optional[str] = None

    confidence: float = 1.0
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ContextResolution:
    role_name: str
    chosen: Optional[ContextEntry]
    candidates: list[ContextEntry] = field(default_factory=list)
    reason: Optional[str] = None


@dataclass
class UnitRuntimeInfo:
    name: str
    dimension: str
    normalize_to: Optional[str] = None
    normalize_op: Optional[str] = None
    normalize_factor: Optional[float] = None


@dataclass
class ActivityRuntimeInfo:
    name: str
    dimension: str
    scope_category: str


@dataclass
class SiteRecord:
    site_id: str
    aliases: list[str]
    entity_id: Optional[str] = None
    country: Optional[str] = None


class ContextStore:
    """
    역할별 context entry 저장소.
    resolve()는 '현재 scope에서 쓸 수 있는 가장 적절한 context'를 골라준다.
    """

    def __init__(self) -> None:
        self._entries_by_role: dict[str, list[ContextEntry]] = {}

    def push(self, entry: ContextEntry) -> None:
        self._entries_by_role.setdefault(entry.role_name, []).append(entry)

    def resolve_all(
        self,
        role_name: str,
        target_scope: ScopePath,
        *,
        column_key: Optional[str] = None,
    ) -> list[ContextEntry]:
        out: list[ContextEntry] = []
        for entry in self._entries_by_role.get(role_name, []):
            if not _same_document(entry.scope_path, target_scope):
                continue
            if not _ttl_allows(entry, target_scope, column_key=column_key):
                continue
            out.append(entry)

        out.sort(
            key=lambda e: (
                -e.precedence,
                _scope_distance(e.scope_path, target_scope),
                -e.created_at.timestamp(),
            )
        )
        return out

    def resolve_best(
        self,
        role_name: str,
        target_scope: ScopePath,
        *,
        column_key: Optional[str] = None,
    ) -> ContextResolution:
        candidates = self.resolve_all(
            role_name,
            target_scope,
            column_key=column_key,
        )
        chosen = candidates[0] if candidates else None
        reason = None if chosen else "no_applicable_context"
        return ContextResolution(
            role_name=role_name,
            chosen=chosen,
            candidates=candidates,
            reason=reason,
        )


@dataclass
class RuntimeEnv:
    """
    실제 compiler passes가 들고 다니는 실행 환경.
    """
    unit_index: dict[str, UnitRuntimeInfo] = field(default_factory=dict)
    activity_index: dict[str, ActivityRuntimeInfo] = field(default_factory=dict)

    # alias -> canonical
    site_alias_index: dict[str, str] = field(default_factory=dict)
    activity_alias_index: dict[str, str] = field(default_factory=dict)
    unit_alias_index: dict[str, str] = field(default_factory=dict)

    site_records: dict[str, SiteRecord] = field(default_factory=dict)
    factor_index: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    policy_flags: dict[str, Any] = field(default_factory=dict)
    context_store: ContextStore = field(default_factory=ContextStore)

    builtin_registry: dict[str, Callable[..., Any]] = field(default_factory=dict)

    allow_llm_fallback: bool = False
    llm_fallback: Optional[Callable[[str, str], list[LexCandidate]]] = None
    llm_budget_remaining: int = 0

    def can_call_llm(self) -> bool:
        return self.allow_llm_fallback and self.llm_fallback is not None and self.llm_budget_remaining > 0

    def consume_llm_budget(self, n: int = 1) -> bool:
        if self.llm_budget_remaining >= n:
            self.llm_budget_remaining -= n
            return True
        return False


def build_runtime_env(
    spec: ProgramSpec,
    *,
    site_records: Sequence[SiteRecord] | None = None,
    factor_rows: Sequence[dict[str, Any]] | None = None,
    policy_flags: dict[str, Any] | None = None,
    activity_aliases: dict[str, list[str]] | None = None,
    unit_aliases: dict[str, list[str]] | None = None,
    llm_fallback: Optional[Callable[[str, str], list[LexCandidate]]] = None,
    llm_budget: int = 0,
) -> RuntimeEnv:
    env = RuntimeEnv()

    # units
    for unit in spec.units.values():
        env.unit_index[unit.name] = UnitRuntimeInfo(
            name=unit.name,
            dimension=unit.dimension,
            normalize_to=unit.normalize.target_unit if unit.normalize else None,
            normalize_op=unit.normalize.op if unit.normalize else None,
            normalize_factor=unit.normalize.factor if unit.normalize else None,
        )
        env.unit_alias_index[_norm_key(unit.name)] = unit.name

    # unit aliases
    for canonical, aliases in (unit_aliases or {}).items():
        for alias in aliases:
            env.unit_alias_index[_norm_key(alias)] = canonical

    # activities
    for act in spec.activities.values():
        env.activity_index[act.name] = ActivityRuntimeInfo(
            name=act.name,
            dimension=act.dimension,
            scope_category=act.scope_category,
        )
        env.activity_alias_index[_norm_key(act.name)] = act.name

    # activity aliases
    for canonical, aliases in (activity_aliases or {}).items():
        for alias in aliases:
            env.activity_alias_index[_norm_key(alias)] = canonical

    # sites
    for rec in site_records or []:
        env.site_records[rec.site_id] = rec
        for alias in rec.aliases:
            env.site_alias_index[_norm_key(alias)] = rec.site_id

    # factors
    for row in factor_rows or []:
        key = (str(row["activity_type"]), str(row["unit"]))
        env.factor_index[key] = dict(row)

    # policy / llm
    env.policy_flags = dict(policy_flags or {})
    env.allow_llm_fallback = llm_fallback is not None
    env.llm_fallback = llm_fallback
    env.llm_budget_remaining = max(0, llm_budget)

    return env


# ---------------------------------
# Helpers
# ---------------------------------

def _norm_key(s: str) -> str:
    return s.strip().lower()


def _same_document(a: ScopePath, b: ScopePath) -> bool:
    return _ref_at(a, "document") == _ref_at(b, "document")


def _ref_at(path: ScopePath, level: str) -> Optional[str]:
    for frame in path:
        if frame.level == level:
            return frame.ref_id
    return None


def _scope_distance(a: ScopePath, b: ScopePath) -> int:
    """
    값이 작을수록 가깝다.
    대충 '가장 깊은 공통 prefix 이후 차이' 정도로 본다.
    """
    a_pairs = [(x.level, x.ref_id) for x in a]
    b_pairs = [(x.level, x.ref_id) for x in b]

    i = 0
    while i < min(len(a_pairs), len(b_pairs)) and a_pairs[i] == b_pairs[i]:
        i += 1

    return (len(a_pairs) - i) + (len(b_pairs) - i)


def _ttl_allows(
    entry: ContextEntry,
    target_scope: ScopePath,
    *,
    column_key: Optional[str],
) -> bool:
    if entry.ttl == "document":
        return _same_document(entry.scope_path, target_scope)

    if entry.ttl == "section":
        return (
            _same_document(entry.scope_path, target_scope)
            and _ref_at(entry.scope_path, "section") == _ref_at(target_scope, "section")
        )

    if entry.ttl == "table":
        return (
            _same_document(entry.scope_path, target_scope)
            and _ref_at(entry.scope_path, "table") == _ref_at(target_scope, "table")
        )

    if entry.ttl == "row":
        return (
            _same_document(entry.scope_path, target_scope)
            and _ref_at(entry.scope_path, "row") == _ref_at(target_scope, "row")
        )

    if entry.ttl == "column":
        return (
            _same_document(entry.scope_path, target_scope)
            and _ref_at(entry.scope_path, "table") == _ref_at(target_scope, "table")
            and entry.column_key is not None
            and column_key is not None
            and entry.column_key == column_key
        )

    if entry.ttl == "cell_only":
        return entry.scope_path == target_scope

    return False


__all__ = [
    "LexCandidate",
    "ScopeFrame",
    "ScopePath",
    "ContextEntry",
    "ContextResolution",
    "UnitRuntimeInfo",
    "ActivityRuntimeInfo",
    "SiteRecord",
    "ContextStore",
    "RuntimeEnv",
    "build_runtime_env",
]
