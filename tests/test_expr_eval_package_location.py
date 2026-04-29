from expr_eval import EvalContext as LegacyEvalContext, EvalError as LegacyEvalError, ExprEvaluator as LegacyExprEvaluator

from comp.eval.expr import EvalContext as PackageEvalContext, EvalError as PackageEvalError, ExprEvaluator as PackageExprEvaluator


def test_expr_eval_wrapper_matches_package_module():
    assert LegacyEvalError is PackageEvalError
    assert LegacyEvalContext is PackageEvalContext
    assert LegacyExprEvaluator is PackageExprEvaluator
