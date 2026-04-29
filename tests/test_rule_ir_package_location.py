from rule_ir import RuleBuiltinCall as LegacyRuleBuiltinCall, RuleExpr as LegacyRuleExpr

from comp.dsl.rule_ir import RuleBuiltinCall as PackageRuleBuiltinCall, RuleExpr as PackageRuleExpr


def test_rule_ir_wrapper_matches_package_module():
    assert LegacyRuleExpr is PackageRuleExpr
    assert LegacyRuleBuiltinCall is PackageRuleBuiltinCall
