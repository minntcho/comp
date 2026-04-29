# expr_eval.py
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

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
from runtime_env import RuntimeEnv, ScopePath


class EvalError(ValueError):
    pass


@dataclass
class EvalContext:
    """
    Expression evaluation context.

    - text: 현재 fragment 원문
    - scope_path: 현재 평가 대상 scope
    - row: 현재 table row dict (tabular parser에서 사용)
    - row_label: row 첫 컬럼 라벨 등
    - column_key: 현재 컬럼 context 해석용
    - frame: 현재 frame or typed frame
    - claims_by_id: origin()/evidence() 같은 함수에서 사용
    - local_vars: score, stable, status 같은 resolver 변수
    - warning_codes / error_codes: governance/diagnostic 표현식에서 사용
    - approvals: approval.human_reviewer 같은 외부 승인 상태
    """
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
    """
    ESGDL expression evaluator.

    원칙:
    - bare identifier는 local var / frame role / policy / warning/error flag 순으로 해석
    - 못 찾으면 "문자 상수"처럼 그대로 둔다
      (예: committed, pair, EmissionObservation)
    - AlternationExpr는 source 선택 표현식으로 보고 "첫 번째 present 값"을 리턴
    """

    def eval(self, expr: Expr | Any, ctx: EvalContext) -> Any:
        if isinstance(expr, Expr):
            return self._eval_expr(expr, ctx)

        # lowering 이전/중간 단계에서 plain 값이 들어와도 견딜 수 있게
        if isinstance(expr, (str, int, float, bool)):
            return expr

        return expr

    def eval_bool(self, expr: Expr | Any, ctx: EvalContext) -> bool:
        value = self.eval(expr, ctx)
        return self._truthy(value)

    def eval_source(self, expr: Expr | Any, ctx: EvalContext) -> Any:
        """
        parser bind/inherit/tag 에서 source expression 평가.
        현재는 eval과 동일하지만, 추후 source-specific coercion 포인트로 분리.
        """
        return self.eval(expr, ctx)

    # ------------------------------------------------------------------
    # Core expression dispatcher
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Name resolution
    # ------------------------------------------------------------------

    def _resolve_name(self, name: str, ctx: EvalContext) -> Any:
        # 1) local vars: score, stable, status, aggregation ...
        if name in ctx.local_vars:
            return ctx.local_vars[name]

        # 2) frame role value
        frame_value = self._frame_value(ctx.frame, name)
        if frame_value is not None:
            return frame_value

        # 3) policy flags: policy.auto_merge
        if name.startswith("policy."):
            key = name.split(".", 1)[1]
            return ctx.env.policy_flags.get(key)

        # 4) diagnostic flags: warning.AggregateRow / error.InvalidPeriod
        if name.startswith("warning."):
            code = name.split(".", 1)[1]
            return code in ctx.warning_codes

        if name.startswith("error."):
            code = name.split(".", 1)[1]
            return code in ctx.error_codes

        # 5) approvals: approval.human_reviewer
        if name.startswith("approval."):
            key = name.split(".", 1)[1]
            return bool(ctx.approvals.get(key, False))

        # 6) fallback: bare identifier를 문자열 상수처럼 취급
        #    예: committed, pair, EmissionObservation
        return name

    def _frame_value(self, frame: Any, role_name: str) -> Any:
        if frame is None:
            return None

        # typed frame style: frame.bindings[role_name]
        bindings = getattr(frame, "bindings", None)
        if isinstance(bindings, dict) and role_name in bindings:
            binding = bindings[role_name]
            # binding 자체가 scalar거나, Claim-like object일 수 있음
            if hasattr(binding, "value"):
                return getattr(binding, "value")
            return binding

        # partial frame style: frame.slots[role_name]
        slots = getattr(frame, "slots", None)
        if isinstance(slots, dict):
            # key가 Enum일 수도 있어서 문자열 비교 둘 다 지원
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

    # ------------------------------------------------------------------
    # Binary operators
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Builtins / function calls
    # ------------------------------------------------------------------

    def _call_function(self, expr: FunctionCallExpr, ctx: EvalContext) -> Any:
        name = expr.name

        # special cases: DSL에서 bare identifier를 role/label로 쓰는 함수들
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

        # lexical builtins: 현재 text를 첫 인자로 받는다
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

        # generic semantic builtins
        fn = self._lookup_builtin(name, ctx)
        args = [self.eval(arg, ctx) for arg in expr.args]

        # 표준 라이브러리 함수들이 env/frame/claims를 필요로 할 수 있으므로
        # 안전하게 몇 가지 호출 패턴을 순서대로 시도
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

    # ------------------------------------------------------------------
    # Truthiness helpers
    # ------------------------------------------------------------------

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