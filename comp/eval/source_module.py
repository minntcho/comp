from __future__ import annotations

from typing import Any, Optional

from comp.eval.expr import EvalContext
from comp.runtime_env import LexCandidate
from source_ir import (
    SourceBuiltinCall,
    SourceCandidate,
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


class SourceEvalError(ValueError):
    pass


class SourceEvaluator:
    ALLOWED_BUILTINS = {
        "site_alias",
        "activity_alias",
        "unit_symbol",
        "period_expr",
        "number",
        "one_of",
        "llm.fuzzy_lex",
    }

    def resolve(
        self,
        expr: SourceExpr | None,
        *,
        ctx: EvalContext,
        fragment: Any = None,
        tokens_by_fragment: Optional[dict[str, dict[str, list[Any]]]] = None,
    ) -> list[SourceCandidate]:
        if expr is None:
            return []

        if isinstance(expr, SourceFirstOf):
            for option in expr.options:
                out = self.resolve(
                    option,
                    ctx=ctx,
                    fragment=fragment,
                    tokens_by_fragment=tokens_by_fragment,
                )
                if out:
                    return out
            return []

        if isinstance(expr, SourceTokenRef):
            return self._resolve_token(expr.token_name, fragment=fragment, tokens_by_fragment=tokens_by_fragment)

        if isinstance(expr, SourceColumnRef):
            row = self._row(fragment, ctx)
            value = row.get(expr.column_name)
            if value in (None, ""):
                return []
            return [
                SourceCandidate(
                    value=value,
                    confidence=0.95,
                    extraction_mode="explicit",
                    source_fragment_id=self._fragment_id(fragment),
                    metadata={
                        "source_kind": "column",
                        "column_name": expr.column_name,
                    },
                )
            ]

        if isinstance(expr, SourceContextRef):
            resolutions = ctx.env.context_store.resolve_all(
                expr.role_name,
                ctx.scope_path,
                column_key=ctx.column_key,
            )
            return [
                SourceCandidate(
                    value=entry.value,
                    confidence=float(entry.confidence),
                    extraction_mode="inherited",
                    source_fragment_id=entry.source_fragment_id,
                    metadata={
                        "source_kind": "context",
                        "context_id": entry.context_id,
                        "operation": entry.operation,
                        "precedence": entry.precedence,
                    },
                )
                for entry in resolutions
            ]

        if isinstance(expr, SourceRowLabelMatch):
            row_label = self._row_label(fragment, ctx)
            if row_label is None or expr.label not in str(row_label):
                return []
            return [
                SourceCandidate(
                    value=expr.label,
                    confidence=0.92,
                    extraction_mode="explicit",
                    source_fragment_id=self._fragment_id(fragment),
                    metadata={
                        "source_kind": "row_label",
                        "row_label": row_label,
                    },
                )
            ]

        value = self.eval_value(
            expr,
            ctx=ctx,
            fragment=fragment,
            tokens_by_fragment=tokens_by_fragment,
        )
        return self._coerce_to_candidates(value, fragment_id=self._fragment_id(fragment))

    def eval_value(
        self,
        expr: SourceExpr | Any,
        *,
        ctx: EvalContext,
        fragment: Any = None,
        tokens_by_fragment: Optional[dict[str, dict[str, list[Any]]]] = None,
    ) -> Any:
        if not isinstance(expr, SourceExpr):
            return expr

        if isinstance(expr, SourceLiteral):
            return expr.value

        if isinstance(expr, SourceSymbolConst):
            return expr.name

        if isinstance(expr, SourceSetExpr):
            return [
                self.eval_value(item, ctx=ctx, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
                for item in expr.items
            ]

        if isinstance(expr, SourceBuiltinCall):
            return self._call(
                expr,
                ctx=ctx,
                fragment=fragment,
                tokens_by_fragment=tokens_by_fragment,
            )

        if isinstance(expr, SourceTokenRef):
            candidates = self._resolve_token(expr.token_name, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
            return None if not candidates else candidates[0].value

        if isinstance(expr, SourceColumnRef):
            return self._row(fragment, ctx).get(expr.column_name)

        if isinstance(expr, SourceContextRef):
            res = ctx.env.context_store.resolve_best(
                expr.role_name,
                ctx.scope_path,
                column_key=ctx.column_key,
            )
            return None if res.chosen is None else res.chosen.value

        if isinstance(expr, SourceRowLabelMatch):
            row_label = self._row_label(fragment, ctx)
            if row_label is None:
                return None
            return expr.label if expr.label in str(row_label) else None

        if isinstance(expr, SourceFirstOf):
            for option in expr.options:
                value = self.eval_value(
                    option,
                    ctx=ctx,
                    fragment=fragment,
                    tokens_by_fragment=tokens_by_fragment,
                )
                if self._present(value):
                    return value
            return None

        raise SourceEvalError(f"unsupported SourceExpr type: {type(expr).__name__}")

    def _resolve_token(
        self,
        token_name: str,
        *,
        fragment: Any = None,
        tokens_by_fragment: Optional[dict[str, dict[str, list[Any]]]] = None,
    ) -> list[SourceCandidate]:
        if fragment is None or not tokens_by_fragment:
            return []

        fragment_id = self._fragment_id(fragment)
        token_bucket = tokens_by_fragment.get(fragment_id, {}).get(token_name, [])

        out: list[SourceCandidate] = []
        for tok in token_bucket:
            span = (tok.start, tok.end) if tok.start is not None and tok.end is not None else None
            out.append(
                SourceCandidate(
                    value=tok.value,
                    confidence=float(tok.confidence),
                    extraction_mode="explicit",
                    source_token_id=tok.token_id,
                    source_fragment_id=tok.fragment_id,
                    span=span,
                    metadata={
                        "source_kind": "token",
                        "token_name": tok.token_name,
                        "source_channel": tok.source_channel,
                        "rank": tok.rank,
                    },
                )
            )
        return out

    def _call(
        self,
        expr: SourceBuiltinCall,
        *,
        ctx: EvalContext,
        fragment: Any = None,
        tokens_by_fragment: Optional[dict[str, dict[str, list[Any]]]] = None,
    ) -> Any:
        name = expr.name
        if name not in self.ALLOWED_BUILTINS:
            raise SourceEvalError(f"builtin '{name}' is not allowed in SourceEvaluator")

        fn = self._lookup_builtin(name, ctx)

        if name in {"site_alias", "activity_alias", "unit_symbol", "period_expr", "number"}:
            return fn(ctx.text, ctx.env)

        if name == "one_of":
            choices = [
                self.eval_value(arg, ctx=ctx, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
                for arg in expr.args
            ]
            return fn(ctx.text, *choices, env=ctx.env)

        if name == "llm.fuzzy_lex":
            role_name = self._raw_identifier(expr.args, index=0, ctx=ctx, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
            return fn(role_name, ctx.text, ctx.env)

        args = [
            self.eval_value(arg, ctx=ctx, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
            for arg in expr.args
        ]
        for pattern in (
            lambda: fn(*args, env=ctx.env),
            lambda: fn(*args),
        ):
            try:
                return pattern()
            except TypeError:
                continue

        raise SourceEvalError(f"builtin call failed: {name}")

    def _lookup_builtin(self, name: str, ctx: EvalContext):
        fn = ctx.env.builtin_registry.get(name)
        if fn is None:
            raise SourceEvalError(f"unknown builtin: {name}")
        return fn

    def _raw_identifier(
        self,
        args: list[SourceExpr],
        *,
        index: int,
        ctx: EvalContext,
        fragment: Any = None,
        tokens_by_fragment: Optional[dict[str, dict[str, list[Any]]]] = None,
    ) -> str:
        if index >= len(args):
            raise SourceEvalError("missing function arg")
        value = self.eval_value(
            args[index],
            ctx=ctx,
            fragment=fragment,
            tokens_by_fragment=tokens_by_fragment,
        )
        return str(value)

    def _coerce_to_candidates(self, value: Any, *, fragment_id: Optional[str]) -> list[SourceCandidate]:
        if value is None:
            return []

        if isinstance(value, SourceCandidate):
            return [value]

        if isinstance(value, LexCandidate):
            span = (value.start, value.end) if value.start is not None and value.end is not None else None
            return [
                SourceCandidate(
                    value=value.value,
                    confidence=float(value.confidence),
                    extraction_mode="explicit",
                    source_fragment_id=fragment_id,
                    span=span,
                    metadata=dict(value.metadata),
                )
            ]

        if isinstance(value, list):
            out: list[SourceCandidate] = []
            for item in value:
                out.extend(self._coerce_to_candidates(item, fragment_id=fragment_id))
            return out

        if isinstance(value, tuple) and len(value) == 3:
            return [
                SourceCandidate(
                    value=value[0],
                    confidence=0.80,
                    extraction_mode="derived",
                    source_fragment_id=fragment_id,
                    span=(value[1], value[2]),
                    metadata={"source_kind": "tuple_expr"},
                )
            ]

        return [
            SourceCandidate(
                value=value,
                confidence=0.70,
                extraction_mode="derived",
                source_fragment_id=fragment_id,
                metadata={"source_kind": "generic_expr"},
            )
        ]

    def _row(self, fragment: Any, ctx: EvalContext) -> dict[str, Any]:
        if fragment is None:
            return ctx.row
        metadata = getattr(fragment, "metadata", {}) or {}
        row = metadata.get("row", {}) if isinstance(metadata, dict) else {}
        return row or ctx.row

    def _row_label(self, fragment: Any, ctx: EvalContext) -> Any:
        if fragment is None:
            return ctx.row_label
        metadata = getattr(fragment, "metadata", {}) or {}
        row_label = metadata.get("row_label") if isinstance(metadata, dict) else None
        return row_label if row_label is not None else ctx.row_label

    def _fragment_id(self, fragment: Any) -> Optional[str]:
        if fragment is None:
            return None
        return getattr(fragment, "fragment_id", None)

    def _present(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return value != ""
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return bool(value)


__all__ = ["SourceEvalError", "SourceEvaluator"]
