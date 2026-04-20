from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ast_nodes import (
    AlternationExpr,
    BinaryExpr,
    BindStmt,
    BuildStmt,
    ColumnRefExpr,
    ContextRefExpr,
    Expr,
    FunctionCallExpr,
    LiteralExpr,
    NameExpr,
    ParserInheritStmt,
    RowLabelRefExpr,
    SetExpr,
    TagStmt,
    UnaryExpr,
)
from compiled_spec import (
    CompiledBindAction,
    CompiledConstraintSpec,
    CompiledDiagnosticSpec,
    CompiledGovernancePolicy,
    CompiledInheritSpec,
    CompiledInferSpec,
    CompiledParserInheritAction,
    CompiledParserSpec,
    CompiledProgramSpec,
    CompiledResolverPolicy,
    CompiledTagAction,
    CompiledTokenSpec,
)
from lex_ir import (
    LexBuiltinCall,
    LexColumnRef,
    LexContextRef,
    LexExpr,
    LexLiteral,
    LexRowLabelMatch,
    LexSetExpr,
    LexSymbolConst,
    LexUnion,
)
from rule_ir import (
    ContextValueRef,
    FrameSlotRef,
    HasApproval,
    HasDiagnostic,
    LocalVarRef,
    PolicyRef,
    RowFieldRef,
    RuleBinary,
    RuleBuiltinCall,
    RuleCoalesce,
    RuleExpr,
    RuleLiteral,
    RuleSetExpr,
    RuleUnary,
    SymbolConst,
)
from source_ir import (
    SourceBuiltinCall,
    SourceColumnRef,
    SourceContextRef,
    SourceExpr,
    SourceFirstOf,
    SourceLiteral,
    SourceRowLabelMatch,
    SourceSetExpr,
    SourceSymbolConst,
    SourceTokenRef,
)
from spec_nodes import ProgramSpec


class BindingError(ValueError):
    pass


@dataclass
class BindingWarning:
    code: str
    message: str


@dataclass
class BindingReport:
    warnings: list[BindingWarning] = field(default_factory=list)

    def messages(self) -> list[str]:
        return [warning.message for warning in self.warnings]


@dataclass
class BindingHost:
    kind: str
    frame_name: str | None = None
    local_vars: set[str] = field(default_factory=set)
    frame_slots: set[str] = field(default_factory=set)
    row_field_aliases: dict[str, str] = field(default_factory=dict)


class Binder:
    RULE_BUILTINS = {
        "dimension",
        "compatible",
        "valid",
        "valid_period",
        "missing",
        "origin",
        "evidence",
    }

    FRAME_ONLY_RULE_BUILTINS = {
        "missing",
        "origin",
        "evidence",
    }

    LEXICAL_BUILTINS = {
        "site_alias",
        "activity_alias",
        "unit_symbol",
        "period_expr",
        "number",
        "one_of",
        "llm.fuzzy_lex",
    }

    KNOWN_BUILTINS = RULE_BUILTINS | LEXICAL_BUILTINS

    SYMBOL_ALLOWLIST = {
        "committed",
        "merged",
        "review_required",
        "rejected",
        "resolving",
    }

    GOVERNANCE_ROW_FIELDS = {
        "row_id": "row_id",
        "frame_id": "frame_id",
        "frame_type": "frame_type",
        "status": "status",
        "score": "resolution_score",
        "resolution_score": "resolution_score",
        "site_id": "site_id",
        "entity_id": "entity_id",
        "period": "period",
        "activity_type": "activity_type",
        "raw_amount": "raw_amount",
        "raw_unit": "raw_unit",
        "standardized_amount": "standardized_amount",
        "standardized_unit": "standardized_unit",
        "scope_category": "scope_category",
        "parser_name": "parser_name",
    }

    FRAME_RULE_LOCALS = {"frame_type", "status"}
    RESOLVER_LOCALS = {"score", "stable", "status", "iteration", "no_improve_count"}

    def bind(self, spec: ProgramSpec) -> CompiledProgramSpec:
        report = BindingReport()

        return CompiledProgramSpec(
            syntax=spec,
            compiled_tokens={
                token_name: self._bind_token_spec(token_spec, report=report)
                for token_name, token_spec in spec.tokens.items()
            },
            compiled_parsers={
                parser_name: self._bind_parser_spec(spec, parser_spec, report=report)
                for parser_name, parser_spec in spec.parsers.items()
            },
            compiled_inherit_rules=[
                CompiledInheritSpec(
                    syntax=inherit_rule,
                    source_ir=self._bind_source_expr(
                        inherit_rule.source_expr,
                        spec=spec,
                        report=report,
                        allow_token_ref=False,
                    ),
                    condition_ir=self._bind_expr(
                        inherit_rule.condition,
                        host=self._frame_rule_host(spec, None),
                        spec=spec,
                        report=report,
                    ),
                )
                for inherit_rule in spec.inherit_rules
            ],
            compiled_constraints=[
                CompiledConstraintSpec(
                    syntax=constraint,
                    condition_ir=self._bind_expr(
                        constraint.condition,
                        host=self._frame_rule_host(spec, constraint.frame_name),
                        spec=spec,
                        report=report,
                    ),
                )
                for constraint in spec.constraints
            ],
            compiled_diagnostics=[
                CompiledDiagnosticSpec(
                    syntax=diagnostic,
                    condition_ir=self._bind_expr(
                        diagnostic.condition,
                        host=self._frame_rule_host(spec, None),
                        spec=spec,
                        report=report,
                    ),
                )
                for diagnostic in spec.diagnostics
            ],
            compiled_infer_rules=[
                CompiledInferSpec(
                    syntax=rule,
                    value_ir=self._bind_expr(
                        rule.value_expr,
                        host=self._frame_rule_host(spec, None),
                        spec=spec,
                        report=report,
                    ),
                    condition_ir=self._bind_expr(
                        rule.condition,
                        host=self._frame_rule_host(spec, None),
                        spec=spec,
                        report=report,
                    ),
                )
                for rule in spec.infer_rules
            ],
            compiled_resolvers={
                frame_name: self._bind_resolver_policy(spec, frame_name, policy, report)
                for frame_name, policy in spec.resolvers.items()
            },
            compiled_governances={
                frame_name: self._bind_governance_policy(spec, frame_name, policy, report)
                for frame_name, policy in spec.governances.items()
            },
            binding_warnings=report.messages(),
        )

    def _bind_token_spec(self, token_spec, *, report: BindingReport) -> CompiledTokenSpec:
        return CompiledTokenSpec(
            syntax=token_spec,
            primary_ir=(
                self._bind_token_expr(token_spec.primary_expr, report=report)
                if token_spec.primary_expr is not None
                else None
            ),
            fallback_ir=(
                self._bind_token_expr(token_spec.fallback_expr, report=report)
                if token_spec.fallback_expr is not None
                else None
            ),
        )

    def _bind_parser_spec(
        self,
        spec: ProgramSpec,
        parser_spec,
        report: BindingReport,
    ) -> CompiledParserSpec:
        host = self._frame_rule_host(spec, parser_spec.build_frame)
        compiled_actions = []

        for action in parser_spec.actions:
            if isinstance(action, BuildStmt):
                continue

            if isinstance(action, BindStmt):
                compiled_actions.append(
                    CompiledBindAction(
                        syntax=action,
                        source_ir=self._bind_source_expr(
                            action.source_expr,
                            spec=spec,
                            report=report,
                            allow_token_ref=True,
                        ),
                    )
                )
                continue

            if isinstance(action, ParserInheritStmt):
                compiled_actions.append(
                    CompiledParserInheritAction(
                        syntax=action,
                        source_ir=self._bind_source_expr(
                            action.source_expr,
                            spec=spec,
                            report=report,
                            allow_token_ref=True,
                        ),
                        condition_ir=(
                            self._bind_expr(
                                action.condition,
                                host=host,
                                spec=spec,
                                report=report,
                            )
                            if action.condition is not None
                            else None
                        ),
                    )
                )
                continue

            if isinstance(action, TagStmt):
                compiled_actions.append(
                    CompiledTagAction(
                        syntax=action,
                        source_ir=self._bind_source_expr(
                            action.source_expr,
                            spec=spec,
                            report=report,
                            allow_token_ref=True,
                        ),
                    )
                )
                continue

            raise BindingError(f"unsupported parser action for binding: {type(action).__name__}")

        return CompiledParserSpec(
            syntax=parser_spec,
            actions=compiled_actions,
        )

    def _bind_resolver_policy(
        self,
        spec: ProgramSpec,
        frame_name: str,
        policy,
        report: BindingReport,
    ) -> CompiledResolverPolicy:
        host = self._resolver_host(spec, frame_name)
        return CompiledResolverPolicy(
            syntax=policy,
            assigns_ir={
                name: self._bind_expr(expr, host=host, spec=spec, report=report)
                for name, expr in policy.assigns.items()
            },
            candidate_pool_assigns_ir={
                name: self._bind_expr(expr, host=host, spec=spec, report=report)
                for name, expr in policy.candidate_pool_assigns.items()
            },
            commit_condition_ir=(
                self._bind_expr(policy.commit_condition, host=host, spec=spec, report=report)
                if policy.commit_condition is not None
                else None
            ),
            review_condition_ir=(
                self._bind_expr(policy.review_condition, host=host, spec=spec, report=report)
                if policy.review_condition is not None
                else None
            ),
        )

    def _bind_governance_policy(
        self,
        spec: ProgramSpec,
        frame_name: str,
        policy,
        report: BindingReport,
    ) -> CompiledGovernancePolicy:
        host = self._governance_host(frame_name)
        return CompiledGovernancePolicy(
            syntax=policy,
            emit_condition_ir=(
                self._bind_expr(policy.emit_condition, host=host, spec=spec, report=report)
                if policy.emit_condition is not None
                else None
            ),
            merge_conditions_ir=[
                self._bind_expr(expr, host=host, spec=spec, report=report)
                for expr in policy.merge_conditions
            ],
            forbid_merge_conditions_ir=[
                self._bind_expr(expr, host=host, spec=spec, report=report)
                for expr in policy.forbid_merge_conditions
            ],
        )

    def _frame_rule_host(self, spec: ProgramSpec, frame_name: str | None) -> BindingHost:
        return BindingHost(
            kind="frame_rule",
            frame_name=frame_name,
            local_vars=set(self.FRAME_RULE_LOCALS),
            frame_slots=self._frame_slots(spec, frame_name),
        )

    def _resolver_host(self, spec: ProgramSpec, frame_name: str) -> BindingHost:
        return BindingHost(
            kind="resolver",
            frame_name=frame_name,
            local_vars=set(self.RESOLVER_LOCALS),
            frame_slots=self._frame_slots(spec, frame_name),
        )

    def _governance_host(self, frame_name: str) -> BindingHost:
        return BindingHost(
            kind="governance",
            frame_name=frame_name,
            row_field_aliases=dict(self.GOVERNANCE_ROW_FIELDS),
        )

    def _frame_slots(self, spec: ProgramSpec, frame_name: str | None) -> set[str]:
        frame_names: Iterable[str]
        if frame_name is None:
            frame_names = spec.frames.keys()
        else:
            frame_names = [frame_name]

        names: set[str] = set()
        for target_frame_name in frame_names:
            frame_spec = spec.frames.get(target_frame_name)
            if frame_spec is not None:
                names.update(field.name for field in frame_spec.fields)

            for parser in spec.parsers.values():
                if parser.build_frame != target_frame_name:
                    continue
                for action in parser.actions:
                    role_name = getattr(action, "role_name", None)
                    if role_name:
                        names.add(role_name)

        names.update(rule.target_name for rule in spec.infer_rules if rule.target_name)
        return names

    def _declared_symbol_names(self, spec: ProgramSpec) -> set[str]:
        return (
            set(spec.frames.keys())
            | set(spec.activities.keys())
            | set(spec.units.keys())
            | set(spec.dimensions.keys())
        )

    def _bind_expr(
        self,
        expr: Expr,
        *,
        host: BindingHost,
        spec: ProgramSpec,
        report: BindingReport,
    ) -> RuleExpr:
        if isinstance(expr, LiteralExpr):
            return RuleLiteral(value=expr.value)

        if isinstance(expr, NameExpr):
            return self._bind_name(expr.name, host=host, spec=spec, report=report)

        if isinstance(expr, FunctionCallExpr):
            return self._bind_call(expr, host=host, spec=spec, report=report)

        if isinstance(expr, SetExpr):
            return RuleSetExpr(
                items=[self._bind_expr(item, host=host, spec=spec, report=report) for item in expr.items]
            )

        if isinstance(expr, ContextRefExpr):
            return ContextValueRef(role_name=expr.role_name)

        if isinstance(expr, AlternationExpr):
            return RuleCoalesce(
                options=[self._bind_expr(option, host=host, spec=spec, report=report) for option in expr.options]
            )

        if isinstance(expr, UnaryExpr):
            return RuleUnary(
                op=expr.op,
                operand=self._bind_expr(expr.operand, host=host, spec=spec, report=report),
            )

        if isinstance(expr, BinaryExpr):
            return RuleBinary(
                left=self._bind_expr(expr.left, host=host, spec=spec, report=report),
                op=expr.op,
                right=self._bind_expr(expr.right, host=host, spec=spec, report=report),
            )

        if isinstance(expr, ColumnRefExpr):
            raise BindingError(f"column(...) is not allowed in rule host {host.kind}")

        if isinstance(expr, RowLabelRefExpr):
            raise BindingError(f"row_label(...) is not allowed in rule host {host.kind}")

        raise BindingError(f"unsupported rule expression: {type(expr).__name__}")

    def _bind_name(
        self,
        name: str,
        *,
        host: BindingHost,
        spec: ProgramSpec,
        report: BindingReport,
    ) -> RuleExpr:
        if name.startswith("policy."):
            key = name.split(".", 1)[1]
            if not key:
                raise BindingError("policy reference must include a key")
            return PolicyRef(key=key)

        if name.startswith("warning."):
            code = name.split(".", 1)[1]
            if not code:
                raise BindingError("warning reference must include a code")
            return HasDiagnostic(severity="warning", code=code)

        if name.startswith("error."):
            code = name.split(".", 1)[1]
            if not code:
                raise BindingError("error reference must include a code")
            return HasDiagnostic(severity="error", code=code)

        if name.startswith("approval."):
            key = name.split(".", 1)[1]
            if not key:
                raise BindingError("approval reference must include a key")
            return HasApproval(key=key)

        if name in host.local_vars:
            return LocalVarRef(name=name)

        if name in host.row_field_aliases:
            return RowFieldRef(field_name=host.row_field_aliases[name])

        if name in host.frame_slots:
            return FrameSlotRef(role_name=name)

        if name in self._declared_symbol_names(spec) or name in self.SYMBOL_ALLOWLIST:
            return SymbolConst(name=name)

        raise BindingError(
            f"unable to bind name '{name}' in host {host.kind}"
            + (f" for frame {host.frame_name}" if host.frame_name else "")
        )

    def _bind_call(
        self,
        expr: FunctionCallExpr,
        *,
        host: BindingHost,
        spec: ProgramSpec,
        report: BindingReport,
    ) -> RuleBuiltinCall:
        if expr.name in self.LEXICAL_BUILTINS:
            raise BindingError(
                f"lexical builtin '{expr.name}' is not allowed in rule host {host.kind}"
            )

        if expr.name not in self.RULE_BUILTINS:
            raise BindingError(f"unknown rule builtin: {expr.name}")

        if expr.name in self.FRAME_ONLY_RULE_BUILTINS and host.kind not in {"frame_rule", "resolver"}:
            raise BindingError(
                f"frame-only rule builtin '{expr.name}' is not allowed in rule host {host.kind}"
            )

        return RuleBuiltinCall(
            name=expr.name,
            args=[self._bind_expr(arg, host=host, spec=spec, report=report) for arg in expr.args],
        )

    def _bind_token_expr(self, expr: Expr, *, report: BindingReport) -> LexExpr:
        if isinstance(expr, LiteralExpr):
            return LexLiteral(value=expr.value)

        if isinstance(expr, NameExpr):
            return LexSymbolConst(name=expr.name)

        if isinstance(expr, FunctionCallExpr):
            if expr.name not in self.KNOWN_BUILTINS:
                raise BindingError(f"unknown builtin in token expression: {expr.name}")
            return LexBuiltinCall(
                name=expr.name,
                args=[self._bind_token_value_expr(arg, report=report) for arg in expr.args],
            )

        if isinstance(expr, SetExpr):
            return LexSetExpr(
                items=[self._bind_token_value_expr(item, report=report) for item in expr.items]
            )

        if isinstance(expr, ColumnRefExpr):
            return LexColumnRef(column_name=expr.column_name)

        if isinstance(expr, ContextRefExpr):
            return LexContextRef(role_name=expr.role_name)

        if isinstance(expr, RowLabelRefExpr):
            return LexRowLabelMatch(label=expr.label)

        if isinstance(expr, AlternationExpr):
            return LexUnion(
                options=[self._bind_token_expr(option, report=report) for option in expr.options]
            )

        if isinstance(expr, (UnaryExpr, BinaryExpr)):
            raise BindingError(f"boolean/comparison expression is not allowed in token host: {type(expr).__name__}")

        raise BindingError(f"unsupported token expression: {type(expr).__name__}")

    def _bind_token_value_expr(self, expr: Expr, *, report: BindingReport) -> LexExpr:
        if isinstance(expr, AlternationExpr):
            raise BindingError("alternation is not allowed inside token builtin arguments")
        return self._bind_token_expr(expr, report=report)

    def _bind_source_expr(
        self,
        expr: Expr,
        *,
        spec: ProgramSpec,
        report: BindingReport,
        allow_token_ref: bool,
    ) -> SourceExpr:
        if isinstance(expr, LiteralExpr):
            return SourceLiteral(value=expr.value)

        if isinstance(expr, NameExpr):
            if allow_token_ref and expr.name in spec.tokens:
                return SourceTokenRef(token_name=expr.name)
            return SourceSymbolConst(name=expr.name)

        if isinstance(expr, FunctionCallExpr):
            if expr.name not in self.KNOWN_BUILTINS:
                raise BindingError(f"unknown builtin in source expression: {expr.name}")
            return SourceBuiltinCall(
                name=expr.name,
                args=[
                    self._bind_source_value_expr(
                        arg,
                        spec=spec,
                        report=report,
                    )
                    for arg in expr.args
                ],
            )

        if isinstance(expr, SetExpr):
            return SourceSetExpr(
                items=[
                    self._bind_source_value_expr(
                        item,
                        spec=spec,
                        report=report,
                    )
                    for item in expr.items
                ]
            )

        if isinstance(expr, ColumnRefExpr):
            return SourceColumnRef(column_name=expr.column_name)

        if isinstance(expr, ContextRefExpr):
            return SourceContextRef(role_name=expr.role_name)

        if isinstance(expr, RowLabelRefExpr):
            return SourceRowLabelMatch(label=expr.label)

        if isinstance(expr, AlternationExpr):
            return SourceFirstOf(
                options=[
                    self._bind_source_expr(
                        option,
                        spec=spec,
                        report=report,
                        allow_token_ref=allow_token_ref,
                    )
                    for option in expr.options
                ]
            )

        if isinstance(expr, (UnaryExpr, BinaryExpr)):
            raise BindingError(f"boolean/comparison expression is not allowed in source host: {type(expr).__name__}")

        raise BindingError(f"unsupported source expression: {type(expr).__name__}")

    def _bind_source_value_expr(
        self,
        expr: Expr,
        *,
        spec: ProgramSpec,
        report: BindingReport,
    ) -> SourceExpr:
        if isinstance(expr, AlternationExpr):
            raise BindingError("alternation is not allowed inside source builtin arguments")
        return self._bind_source_expr(
            expr,
            spec=spec,
            report=report,
            allow_token_ref=False,
        )
