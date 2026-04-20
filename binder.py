from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ast_nodes import (
    AlternationExpr,
    BinaryExpr,
    ColumnRefExpr,
    ContextRefExpr,
    Expr,
    FunctionCallExpr,
    LiteralExpr,
    NameExpr,
    RowLabelRefExpr,
    SetExpr,
    UnaryExpr,
)
from compiled_spec import (
    CompiledConstraintSpec,
    CompiledDiagnosticSpec,
    CompiledGovernancePolicy,
    CompiledInferSpec,
    CompiledProgramSpec,
    CompiledResolverPolicy,
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
