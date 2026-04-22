from rule_builtins import (
    RuleBuiltinSpec as LegacyRuleBuiltinSpec,
    get_default_rule_builtin_registry as legacy_get_default_rule_builtin_registry,
)

from comp.builtins.rule import (
    RuleBuiltinSpec as PackageRuleBuiltinSpec,
    get_default_rule_builtin_registry as package_get_default_rule_builtin_registry,
)


def test_rule_builtins_wrapper_matches_package_module():
    assert LegacyRuleBuiltinSpec is PackageRuleBuiltinSpec
    assert legacy_get_default_rule_builtin_registry is package_get_default_rule_builtin_registry
