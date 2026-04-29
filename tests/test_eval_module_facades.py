from compiled_expr_eval import CompiledExprEvaluator as LegacyCompiledExprEvaluator
from expr_eval import EvalContext as LegacyEvalContext, ExprEvaluator as LegacyExprEvaluator
from lex_eval import LexEvaluator as LegacyLexEvaluator
from rule_eval import RuleEvaluator as LegacyRuleEvaluator
from source_eval import SourceEvaluator as LegacySourceEvaluator

from comp.eval import (
    CompiledExprEvaluator,
    ExprEvaluator,
    LexEvaluator,
    RuleEvaluator,
    SourceEvaluator,
)
from comp.eval.compiled_expr import CompiledExprEvaluator as PackageCompiledExprEvaluator
from comp.eval.expr import EvalContext as PackageEvalContext, ExprEvaluator as PackageExprEvaluator
from comp.eval.lex import LexEvaluator as PackageLexEvaluator
from comp.eval.rule import RuleEvaluator as PackageRuleEvaluator
from comp.eval.source_module import SourceEvaluator as PackageSourceEvaluator


def test_eval_module_facades_match_legacy_objects():
    assert PackageExprEvaluator is LegacyExprEvaluator
    assert PackageEvalContext is LegacyEvalContext
    assert PackageCompiledExprEvaluator is LegacyCompiledExprEvaluator
    assert PackageLexEvaluator is LegacyLexEvaluator
    assert PackageRuleEvaluator is LegacyRuleEvaluator
    assert PackageSourceEvaluator is LegacySourceEvaluator


def test_eval_package_exports_match_legacy_objects():
    assert ExprEvaluator is LegacyExprEvaluator
    assert CompiledExprEvaluator is LegacyCompiledExprEvaluator
    assert LexEvaluator is LegacyLexEvaluator
    assert RuleEvaluator is LegacyRuleEvaluator
    assert SourceEvaluator is LegacySourceEvaluator
