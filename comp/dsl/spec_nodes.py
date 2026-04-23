from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from comp.dsl.ast_nodes import Expr, ParserAction, ResolverStmt, GovernanceStmt


@dataclass
class DimensionSpec:
    name: str


@dataclass
class NormalizeSpec:
    target_unit: str
    op: str
    factor: float


@dataclass
class UnitSpec:
    name: str
    dimension: str
    normalize: Optional[NormalizeSpec] = None


@dataclass
class ActivitySpec:
    name: str
    dimension: str
    scope_category: str


@dataclass
class ContextPolicy:
    role_name: str
    precedence_chain: list[str] = field(default_factory=list)
    ttl_levels: list[str] = field(default_factory=list)
    supports: list[str] = field(default_factory=list)
    refine_pairs: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class FieldSpec:
    name: str
    type_name: str
    generic: Optional[str] = None
    optional: bool = False


@dataclass
class FrameSpec:
    name: str
    fields: list[FieldSpec] = field(default_factory=list)


@dataclass
class TokenSpec:
    name: str
    primary_expr: Optional[Expr] = None
    fallback_expr: Optional[Expr] = None


@dataclass
class ParserSpec:
    name: str
    source_selectors: list[str]
    build_frame: str
    actions: list[ParserAction] = field(default_factory=list)


@dataclass
class InheritSpec:
    role_name: str
    source_expr: Expr
    condition: Expr


@dataclass
class InferSpec:
    target_name: str
    op: str
    value_expr: Expr
    condition: Expr
    weight: Optional[float] = None


@dataclass
class ConstraintSpec:
    kind: str
    condition: Expr
    frame_name: Optional[str] = None


@dataclass
class DiagnosticSpec:
    level: str
    code: str
    condition: Expr


@dataclass
class ResolverPolicy:
    frame_name: str
    assigns: dict[str, Expr] = field(default_factory=dict)
    candidate_pool_assigns: dict[str, Expr] = field(default_factory=dict)
    commit_condition: Optional[Expr] = None
    review_condition: Optional[Expr] = None
    reject_otherwise: bool = False


@dataclass
class GovernancePolicy:
    frame_name: str
    emit_condition: Optional[Expr] = None
    merge_conditions: list[Expr] = field(default_factory=list)
    forbid_merge_conditions: list[Expr] = field(default_factory=list)


@dataclass
class ProgramSpec:
    module_name: str
    imports: list[str] = field(default_factory=list)

    dimensions: dict[str, DimensionSpec] = field(default_factory=dict)
    units: dict[str, UnitSpec] = field(default_factory=dict)
    activities: dict[str, ActivitySpec] = field(default_factory=dict)

    scope_chain: list[str] = field(
        default_factory=lambda: ["document", "section", "table", "row", "cell"]
    )

    contexts: dict[str, ContextPolicy] = field(default_factory=dict)
    frames: dict[str, FrameSpec] = field(default_factory=dict)
    tokens: dict[str, TokenSpec] = field(default_factory=dict)
    parsers: dict[str, ParserSpec] = field(default_factory=dict)

    inherit_rules: list[InheritSpec] = field(default_factory=list)
    infer_rules: list[InferSpec] = field(default_factory=list)
    constraints: list[ConstraintSpec] = field(default_factory=list)
    diagnostics: list[DiagnosticSpec] = field(default_factory=list)

    resolvers: dict[str, ResolverPolicy] = field(default_factory=dict)
    governances: dict[str, GovernancePolicy] = field(default_factory=dict)


__all__ = [
    "DimensionSpec",
    "NormalizeSpec",
    "UnitSpec",
    "ActivitySpec",
    "ContextPolicy",
    "FieldSpec",
    "FrameSpec",
    "TokenSpec",
    "ParserSpec",
    "InheritSpec",
    "InferSpec",
    "ConstraintSpec",
    "DiagnosticSpec",
    "ResolverPolicy",
    "GovernancePolicy",
    "ProgramSpec",
]
