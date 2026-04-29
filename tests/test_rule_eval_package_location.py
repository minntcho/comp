from rule_eval import RuleEvalContext as LegacyRuleEvalContext, RuleEvalError as LegacyRuleEvalError, RuleEvaluator as LegacyRuleEvaluator

from comp.eval.rule import RuleEvalContext as PackageRuleEvalContext, RuleEvalError as PackageRuleEvalError, RuleEvaluator as PackageRuleEvaluator


def test_rule_eval_wrapper_matches_package_module():
    assert LegacyRuleEvalContext is PackageRuleEvalContext
    assert LegacyRuleEvalError is PackageRuleEvalError
    assert LegacyRuleEvaluator is PackageRuleEvaluator
