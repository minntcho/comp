from __future__ import annotations

from dataclasses import dataclass, field

from ast_nodes import BindStmt, ParserInheritStmt, TagStmt
from lex_ir import LexExpr
from rule_ir import RuleExpr
from source_ir import SourceExpr
from spec_nodes import (
    ConstraintSpec,
    DiagnosticSpec,
    GovernancePolicy,
    InferSpec,
    InheritSpec,
    ParserSpec,
    ProgramSpec,
    ResolverPolicy,
    TokenSpec,
)


@dataclass
class CompiledTokenSpec:
    syntax: TokenSpec
    primary_ir: LexExpr | None = None
    fallback_ir: LexExpr | None = None


@dataclass
class CompiledInheritSpec:
    syntax: InheritSpec
    source_ir: SourceExpr
    condition_ir: RuleExpr


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
class CompiledBindAction:
    syntax: BindStmt
    source_ir: SourceExpr


@dataclass
class CompiledParserInheritAction:
    syntax: ParserInheritStmt
    source_ir: SourceExpr
    condition_ir: RuleExpr | None = None


@dataclass
class CompiledTagAction:
    syntax: TagStmt
    source_ir: SourceExpr


CompiledParserAction = CompiledBindAction | CompiledParserInheritAction | CompiledTagAction


@dataclass
class CompiledParserSpec:
    syntax: ParserSpec
    actions: list[CompiledParserAction] = field(default_factory=list)


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

    compiled_tokens: dict[str, CompiledTokenSpec] = field(default_factory=dict)
    compiled_parsers: dict[str, CompiledParserSpec] = field(default_factory=dict)
    compiled_inherit_rules: list[CompiledInheritSpec] = field(default_factory=list)

    compiled_constraints: list[CompiledConstraintSpec] = field(default_factory=list)
    compiled_diagnostics: list[CompiledDiagnosticSpec] = field(default_factory=list)
    compiled_infer_rules: list[CompiledInferSpec] = field(default_factory=list)
    compiled_resolvers: dict[str, CompiledResolverPolicy] = field(default_factory=dict)
    compiled_governances: dict[str, CompiledGovernancePolicy] = field(default_factory=dict)

    binding_warnings: list[str] = field(default_factory=list)

    def __getattr__(self, name: str):
        return getattr(self.syntax, name)
