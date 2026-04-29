from __future__ import annotations

import re
from typing import Any

from comp.builtins.rule import get_default_rule_builtin_registry
from comp.dsl.rule_ir import *


RuleEvalContext = Any


class RuleEvalError(ValueError):
    pass


class RuleEvaluator:
    def __init__(self, *, builtin_registry=None):
        self.builtin_registry = get_default_rule_builtin_registry() if builtin_registry is None else builtin_registry

    def eval(self, expr, ctx):
        if not isinstance(expr, RuleExpr):
            return expr
        if isinstance(expr, RuleLiteral):
            return expr.value
        if isinstance(expr, LocalVarRef):
            return ctx.local_vars.get(expr.name)
        if isinstance(expr, FrameSlotRef):
            return self._frame_value(ctx.frame, expr.role_name)
        if isinstance(expr, RowFieldRef):
            return ctx.row.get(expr.field_name) if isinstance(ctx.row, dict) else getattr(ctx.row, expr.field_name, None)
        if isinstance(expr, ContextValueRef):
            res = ctx.env.context_store.resolve_best(expr.role_name, ctx.scope_path, column_key=getattr(ctx, "column_key", None))
            return None if res.chosen is None else res.chosen.value
        if isinstance(expr, PolicyRef):
            return ctx.env.policy_flags.get(expr.key)
        if isinstance(expr, HasDiagnostic):
            return expr.code in (ctx.warning_codes if expr.severity == "warning" else ctx.error_codes)
        if isinstance(expr, HasApproval):
            return bool(ctx.approvals.get(expr.key, False))
        if isinstance(expr, SymbolConst):
            return expr.name
        if isinstance(expr, RuleBuiltinCall):
            return self._call(expr, ctx)
        if isinstance(expr, RuleSetExpr):
            return [self.eval(x, ctx) for x in expr.items]
        if isinstance(expr, RuleCoalesce):
            for x in expr.options:
                v = self.eval(x, ctx)
                if self._present(v):
                    return v
            return None
        if isinstance(expr, RuleUnary):
            if expr.op == "not":
                return not self.eval_bool(expr.operand, ctx)
            raise RuleEvalError(f"unsupported unary op: {expr.op}")
        if isinstance(expr, RuleBinary):
            return self._binary(expr, ctx)
        raise RuleEvalError(f"unsupported RuleExpr type: {type(expr).__name__}")

    def eval_bool(self, expr, ctx):
        return self._present(self.eval(expr, ctx))

    def _binary(self, expr, ctx):
        l, r, op = self.eval(expr.left, ctx), self.eval(expr.right, ctx), expr.op
        if op == "or":
            return self._present(l) or self._present(r)
        if op == "and":
            return self._present(l) and self._present(r)
        if op == "==":
            return l == r
        if op == "!=":
            return l != r
        if op == ">=":
            return l >= r
        if op == "<=":
            return l <= r
        if op == ">":
            return l > r
        if op == "<":
            return l < r
        if op == "in":
            return False if r is None else l in r
        if op == "matches":
            return re.search(str(r), str(l or "")) is not None
        raise RuleEvalError(f"unsupported binary op: {op}")

    def _call(self, expr, ctx):
        spec = self.builtin_registry.get(expr.name)
        if spec is None:
            raise RuleEvalError(f"unknown rule builtin: {expr.name}")
        if len(expr.args) != len(spec.arg_modes):
            raise RuleEvalError(f"builtin {expr.name} expected {len(spec.arg_modes)} args, got {len(expr.args)}")
        args = [self._arg(a, m, ctx) for a, m in zip(expr.args, spec.arg_modes)]
        return spec.impl(ctx, *args)

    def _arg(self, arg, mode, ctx):
        if mode == "value":
            return self.eval(arg, ctx)
        if mode in {"slot_name", "symbol_name"}:
            if isinstance(arg, RowFieldRef):
                raise RuleEvalError(
                    f"row field ref '{arg.field_name}' cannot be used as {mode}; "
                    "bind a value expression instead or use a row-aware builtin"
                )
            if isinstance(arg, FrameSlotRef):
                return arg.role_name
            if isinstance(arg, SymbolConst):
                return arg.name
            if isinstance(arg, RuleLiteral):
                return str(arg.value)
            return str(self.eval(arg, ctx))
        raise RuleEvalError(f"unsupported builtin arg mode: {mode}")

    def _frame_value(self, frame, role_name):
        if frame is None:
            return None
        b = getattr(frame, "bindings", None)
        if isinstance(b, dict) and role_name in b:
            v = b[role_name]
            return getattr(v, "value", v)
        s = getattr(frame, "slots", None)
        if isinstance(s, dict):
            if role_name in s:
                v = getattr(s[role_name], "resolved_value", None)
                if v not in (None, ""):
                    return v
            for k, slot in s.items():
                if getattr(k, "value", k) == role_name:
                    v = getattr(slot, "resolved_value", None)
                    if v not in (None, ""):
                        return v
        return None

    def _present(self, v):
        if v is None:
            return False
        if isinstance(v, str):
            return v != ""
        if isinstance(v, (list, tuple, set, dict)):
            return len(v) > 0
        return bool(v)


__all__ = ["RuleEvalContext", "RuleEvalError", "RuleEvaluator"]
