from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from comp.dsl.ast_nodes import (
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
from comp.runtime_env import RuntimeEnv, ScopePath


class EvalError(ValueError):
    pass


@dataclass
class EvalContext:
    env: RuntimeEnv

    text: str = ""
    scope_path: ScopePath = field(default_factory=tuple)

    row: dict[str, Any] = field(default_factory=dict)
    row_label: Optional[str] = None
    column_key: Optional[str] = None

    frame: Any = None
    claims_by_id: dict[str, Any] = field(default_factory=dict)

    local_vars: dict[str, Any] = field(default_factory=dict)
    warning_codes: set[str] = field(default_factory=set)
    error_codes: set[str] = field(default_factory=set)
    approvals: dict[str, bool] = field(default_factory=dict)


class ExprEvaluator:
    def eval(self, expr: Expr | Any, ctx: EvalContext) -> Any:
        if isinstance(expr, Expr):
            return self._eval_expr(expr, ctx)

        if isinstance(expr, (str, int, float, bool)):
            return expr

        return expr

    def eval_bool(self, expr: Expr | Any, ctx: EvalContext) -> bool:
        value = self.eval(expr, ctx)
        return self._truthy(value)

    def eval_source(self, expr: Expr | Any, ctx: EvalContext) -> Any:
        return self.eval(expr, ctx)

    def _eval_expr(self, expr: Expr, ctx: EvalContext) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value

        if isinstance(expr, NameExpr):
            return self._resolve_name(expr.name, ctx)

        if isinstance(expr, FunctionCallExpr):
            return self._call_function(expr, ctx)

        if isinstance(expr, SetExpr):
            return [self.eval(item, ctx) for item in expr.items]

        if isinstance(expr, ColumnRefExpr):
            return ctx.row.get(expr.column_name)

        if isinstance(expr, ContextRefExpr):
            res = ctx.env.context_store.resolve_best(
                expr.role_name,
                ctx.scope_path,
                column_key=ctx.column_key,
            )
            return None if res.chosen is None else res.chosen.value

        if isinstance(expr, RowLabelRefExpr):
            if ctx.row_label is None:
                return None
            if expr.label in ctx.row_label:
                return expr.label
            return None

        if isinstance(expr, AlternationExpr):
            for option in expr.options:
                value = self.eval(option, ctx)
                if self._present(value):
                    return value
            return None

        if isinstance(expr, UnaryExpr):
            if expr.op == "not":
                return not self.eval_bool(expr.operand, ctx)
            raise EvalError(f"unsupported unary op: {expr.op}")

        if isinstance(expr, BinaryExpr):
            return self._eval_binary(expr, ctx)

        raise EvalError(f"unsupported Expr type: {type(expr).__name__}")

    def _resolve_name(self, name: str, ctx: EvalContext) -> Any:
        if name in ctx.local_vars:
            return ctx.local_vars[name]

        frame_value = self._frame_value(ctx.frame, name)
        if frame_value is not None:
            return frame_value

        if name.startswith("policy."):
            key = name.split(".", 1)[1]
            return ctx.env.policy_flags.get(key)

        if name.startswith("warning."):
            code = name.split(".", 1)[1]
            return code in ctx.warning_codes

        if name.startswith("error."):
            code = name.split(".", 1)[1]
            return code in ctx.error_codes

        if name.startswith("approval."):
            key = name.split(".", 1)[1]
            return bool(ctx.approvals.get(key, False))

        return name

    def _frame_value(self, frame: Any, role_name: str) -> Any:
        if frame is None:
            return None

        bindings = getattr(frame, "bindings", None)
        if isinstance(bindings, dict) and role_name in bindings:
            binding = bindings[role_name]
            if hasattr(binding, "value"):
                return getattr(binding, "value")
            return binding

        slots = getattr(frame, "slots", None)
        if isinstance(slots, dict):
            if role_name in slots:
                slot = slots[role_name]
                resolved_value = getattr(slot, "resolved_value", None)
                if resolved_value not in (None, ""):
                    return resolved_value

            for k, slot in slots.items():
                key_str = getattr(k, "value", k)
                if key_str == role_name:
                    resolved_value = getattr(slot, "resolved_value", None)
                    if resolved_value not in (None, ""):
                        return resolved_value

        return None

    def _eval_binary(self, expr: BinaryExpr, ctx: EvalContext) -> Any:
        left = self.eval(expr.left, ctx)
        right = self.eval(expr.right, ctx)
        op = expr.op

        if op == "or":
            return self._truthy(left) or self._truthy(right)

        if op == "and":
            return self._truthy(left) and self._truthy(right)

        if op == "==":
            return left == right

        if op == "!=":
            return left != right

        if op == ">=":
            return left >= right

        if op == "<=":
            return left <= right

        if op == ">":
            return left > right

        if op == "<":
            return left < right

        if op == "in":
            if right is None:
                return False
            return left in right

        if op == "matches":
            return re.search(str(right), str(left or "")) is not None

        raise EvalError(f"unsupported binary op: {op}")

    def _call_function(self, expr: FunctionCallExpr, ctx: EvalContext) -> Any:
        name = expr.name

        if name == "missing":
            role_name = self._raw_identifier(expr.args, index=0, ctx=ctx)
            fn = self._lookup_builtin(name, ctx)
            return fn(role_name, ctx.frame)

        if name == "origin":
            role_name = self._raw_identifier(expr.args, index=0, ctx=ctx)
            fn = self._lookup_builtin(name, ctx)
            return fn(role_name, ctx.frame, ctx.claims_by_id)

        if name == "evidence":
            kind = self._raw_identifier(expr.args, index=0, ctx=ctx)
            fn = self._lookup_builtin(name, ctx)
            return fn(kind, ctx.frame, ctx.claims_by_id)

        if name in {"site_alias", "activity_alias", "unit_symbol", "period_expr", "number"}:
            fn = self._lookup_builtin(name, ctx)
            return fn(ctx.text, ctx.env)

        if name == "one_of":
            fn = self._lookup_builtin(name, ctx)
            choices = [self.eval(arg, ctx) for arg in expr.args]
            return fn(ctx.text, *choices, env=ctx.env)

        if name == "llm.fuzzy_lex":
            fn = self._lookup_builtin(name, ctx)
            role_name = self._raw_identifier(expr.args, index=0, ctx=ctx)
            return fn(role_name, ctx.text, ctx.env)

        fn = self._lookup_builtin(name, ctx)
        args = [self.eval(arg, ctx) for arg in expr.args]

        for pattern in (
            lambda: fn(*args, env=ctx.env, frame=ctx.frame, claims_by_id=ctx.claims_by_id),
            lambda: fn(*args, env=ctx.env, frame=ctx.frame),
            lambda: fn(*args, env=ctx.env),
            lambda: fn(*args),
        ):
            try:
                return pattern()
            except TypeError:
                continue

        raise EvalError(f"builtin call failed: {name}")

    def _lookup_builtin(self, name: str, ctx: EvalContext):
        fn = ctx.env.builtin_registry.get(name)
        if fn is None:
            raise EvalError(f"unknown builtin: {name}")
        return fn

    def _raw_identifier(self, args: list[Expr], index: int, ctx: EvalContext) -> str:
        if index >= len(args):
            raise EvalError("missing function arg")

        arg = args[index]

        if isinstance(arg, NameExpr):
            return arg.name

        value = self.eval(arg, ctx)
        return str(value)

    def _present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value != ""
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return bool(value)

    def _truthy(self, value: Any) -> bool:
        return self._present(value)


__all__ = ["EvalError", "EvalContext", "ExprEvaluator"]
