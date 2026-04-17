from __future__ import annotations
from types import SimpleNamespace

from expr_eval import ExprEvaluator
from rule_ir import RuleExpr
from rule_eval import RuleEvaluator


class CompiledExprEvaluator(ExprEvaluator):
    def __init__(self, *, rule_evaluator: RuleEvaluator | None = None) -> None:
        super().__init__()
        self.rule_evaluator = RuleEvaluator() if rule_evaluator is None else rule_evaluator

    def eval(self, expr, ctx):
        if isinstance(expr, RuleExpr):
            return self.rule_evaluator.eval(expr, self._ctx(ctx))
        return super().eval(expr, ctx)

    def eval_bool(self, expr, ctx):
        if isinstance(expr, RuleExpr):
            return self.rule_evaluator.eval_bool(expr, self._ctx(ctx))
        return super().eval_bool(expr, ctx)

    def _ctx(self, ctx):
        row = getattr(ctx, "row", None)
        if row in (None, {}):
            row = getattr(ctx, "local_vars", {})
        return SimpleNamespace(
            env=ctx.env,
            text=getattr(ctx, "text", ""),
            scope_path=getattr(ctx, "scope_path", tuple()),
            column_key=getattr(ctx, "column_key", None),
            row=row,
            frame=getattr(ctx, "frame", None),
            claims_by_id=getattr(ctx, "claims_by_id", {}),
            local_vars=getattr(ctx, "local_vars", {}),
            warning_codes=set(getattr(ctx, "warning_codes", set()) or set()),
            error_codes=set(getattr(ctx, "error_codes", set()) or set()),
            approvals=getattr(ctx, "approvals", {}),
        )
