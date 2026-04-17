from __future__ import annotations

from dataclasses import dataclass, field

from rule_ir import RuleExpr
from spec_nodes import (
    ConstraintSpec,
    DiagnosticSpec,
    GovernancePolicy,
    InferSpec,
    ProgramSpec,
    ResolverPolicy,
)


@dataclass
class CompiledConstraintSpec:
    syntax: ConstraintSpec
    condition_ir: RuleExpr


@dataclass
class CompiledDiagnosticSpec:
    syntax: DiagnosticSpec
    condition_ir: RuleExpr


@dataclass
class CompiledInferSpec:
    syntax: InferSpec
    value_ir: RuleExpr
    condition_ir: RuleExpr


@dataclass
class CompiledResolverPolicy:
    syntax: ResolverPolicy
    assigns_ir: dict[str, RuleExpr] = field(default_factory=dict)
    candidate_pool_assigns_ir: dict[str, RuleExpr] = field(default_factory=dict)
    commit_condition_ir: RuleExpr | None = None
    review_condition_ir: RuleExpr | None = None


@dataclass
class CompiledGovernancePolicy:
    syntax: GovernancePolicy
    emit_condition_ir: RuleExpr | None = None
    merge_conditions_ir: list[RuleExpr] = field(default_factory=list)
    forbid_merge_conditions_ir: list[RuleExpr] = field(default_factory=list)


@dataclass
class CompiledProgramSpec:
    syntax: ProgramSpec

    compiled_constraints: list[CompiledConstraintSpec] = field(default_factory=list)
    compiled_diagnostics: list[CompiledDiagnosticSpec] = field(default_factory=list)
    compiled_infer_rules: list[CompiledInferSpec] = field(default_factory=list)
    compiled_resolvers: dict[str, CompiledResolverPolicy] = field(default_factory=dict)
    compiled_governances: dict[str, CompiledGovernancePolicy] = field(default_factory=dict)

    binding_warnings: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        return getattr(self.syntax, name)
