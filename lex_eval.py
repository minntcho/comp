from __future__ import annotations

from typing import Any

from expr_eval import EvalContext
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
from runtime_env import LexCandidate


class LexEvalError(ValueError):
    pass


class LexEvaluator:
    def resolve(self, expr: LexExpr | None, ctx: EvalContext) -> list[LexCandidate]:
        if expr is None:
            return []

        if isinstance(expr, LexUnion):
            hits: list[LexCandidate] = []
            for option in expr.options:
                hits.extend(self.resolve(option, ctx))
            return self._merge_hits(hits)

        value = self.eval_value(expr, ctx)
        return self._coerce_to_candidates(value)

    def eval_value(self, expr: LexExpr | Any, ctx: EvalContext) -> Any:
        if not isinstance(expr, LexExpr):
            return expr

        if isinstance(expr, LexLiteral):
            return expr.value

        if isinstance(expr, LexSymbolConst):
            return expr.name

        if isinstance(expr, LexSetExpr):
            return [self.eval_value(item, ctx) for item in expr.items]

        if isinstance(expr, LexBuiltinCall):
            return self._call(expr, ctx)

        if isinstance(expr, LexColumnRef):
            return ctx.row.get(expr.column_name)

        if isinstance(expr, LexContextRef):
            res = ctx.env.context_store.resolve_best(
                expr.role_name,
                ctx.scope_path,
                column_key=ctx.column_key,
            )
            return None if res.chosen is None else res.chosen.value

        if isinstance(expr, LexRowLabelMatch):
            if ctx.row_label is None:
                return None
            return expr.label if expr.label in ctx.row_label else None

        raise LexEvalError(f"unsupported LexExpr type: {type(expr).__name__}")

    def _call(self, expr: LexBuiltinCall, ctx: EvalContext) -> Any:
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
            choices = [self.eval_value(arg, ctx) for arg in expr.args]
            return fn(ctx.text, *choices, env=ctx.env)

        if name == "llm.fuzzy_lex":
            fn = self._lookup_builtin(name, ctx)
            role_name = self._raw_identifier(expr.args, index=0, ctx=ctx)
            return fn(role_name, ctx.text, ctx.env)

        fn = self._lookup_builtin(name, ctx)
        args = [self.eval_value(arg, ctx) for arg in expr.args]

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

        raise LexEvalError(f"builtin call failed: {name}")

    def _lookup_builtin(self, name: str, ctx: EvalContext):
        fn = ctx.env.builtin_registry.get(name)
        if fn is None:
            raise LexEvalError(f"unknown builtin: {name}")
        return fn

    def _raw_identifier(self, args: list[LexExpr], index: int, ctx: EvalContext) -> str:
        if index >= len(args):
            raise LexEvalError("missing function arg")
        value = self.eval_value(args[index], ctx)
        return str(value)

    def _coerce_to_candidates(self, value: Any) -> list[LexCandidate]:
        if value is None:
            return []

        if isinstance(value, LexCandidate):
            return [value]

        if isinstance(value, list):
            out: list[LexCandidate] = []
            for item in value:
                out.extend(self._coerce_to_candidates(item))
            return out

        if isinstance(value, tuple) and len(value) == 3:
            return [
                LexCandidate(
                    value=value[0],
                    start=value[1],
                    end=value[2],
                    confidence=0.80,
                )
            ]

        return [
            LexCandidate(
                value=value,
                start=None,
                end=None,
                confidence=0.50,
            )
        ]

    def _merge_hits(self, hits: list[LexCandidate]) -> list[LexCandidate]:
        by_key: dict[tuple[Any, int | None, int | None], LexCandidate] = {}
        for hit in hits:
            key = (hit.value, hit.start, hit.end)
            prev = by_key.get(key)
            if prev is None or hit.confidence > prev.confidence:
                by_key[key] = hit
        return list(by_key.values())
