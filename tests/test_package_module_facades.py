from ast_builder import ASTBuilder as LegacyASTBuilder
from binder import Binder as LegacyBinder
from rule_eval import RuleEvaluator as LegacyRuleEvaluator

from comp.dsl import ASTBuilder, Binder
from comp.dsl.ast_builder import ASTBuilder as PackageASTBuilder
from comp.dsl.binder import Binder as PackageBinder
from comp.eval import RuleEvaluator
from comp.eval.rule import RuleEvaluator as PackageRuleEvaluator


def test_dsl_package_exports_match_legacy_objects():
    assert ASTBuilder is LegacyASTBuilder
    assert Binder is LegacyBinder


def test_dsl_module_facades_match_legacy_objects():
    assert PackageASTBuilder is LegacyASTBuilder
    assert PackageBinder is LegacyBinder


def test_eval_rule_facade_matches_legacy_object():
    assert RuleEvaluator is LegacyRuleEvaluator
    assert PackageRuleEvaluator is LegacyRuleEvaluator
