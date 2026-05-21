from comp.compiler_tool import (
    CalculationFormula,
    DomainPack,
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    RuleFamily,
    SemanticRubric,
    calculation_formula_declaration_fingerprint,
    domain_pack_declaration_fingerprint,
    rule_family_declaration_fingerprint,
    semantic_rubric_declaration_fingerprint,
)


def test_calculation_formula_declaration_fingerprint_pins_formula_contract():
    formula = CalculationFormula(
        formula_id="pcf.electricity_factor_multiplication.v1",
        output_field="co2e_kg",
        output_unit="kgCO2e",
    )
    same_formula = CalculationFormula(
        formula_id="pcf.electricity_factor_multiplication.v1",
        output_field="co2e_kg",
        output_unit="kgCO2e",
    )
    changed_formula = CalculationFormula(
        formula_id="pcf.electricity_factor_multiplication.v1",
        output_field="co2e_tonnes",
        output_unit="tCO2e",
    )

    fingerprint = calculation_formula_declaration_fingerprint(formula)

    assert fingerprint.dependency_kind == "calculation_formula"
    assert (
        fingerprint.dependency_id
        == "calculation_formula:pcf.electricity_factor_multiplication.v1"
    )
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == calculation_formula_declaration_fingerprint(same_formula)
    assert fingerprint != calculation_formula_declaration_fingerprint(changed_formula)


def test_rule_and_rubric_declaration_fingerprints_pin_semantic_contracts():
    rule = RuleFamily(
        rule_id="pcf.scope2_method_support.v1",
        required_rubric_ids=("pcf.scope2_method_support.rubric.v1",),
        description="Opens a semantic judgment for Scope 2 method support.",
    )
    changed_rule = RuleFamily(
        rule_id="pcf.scope2_method_support.v1",
        required_rubric_ids=("pcf.scope2_method_support.rubric.v2",),
        description="Opens a semantic judgment for Scope 2 method support.",
    )
    changed_rule_evaluator = RuleFamily(
        rule_id="pcf.scope2_method_support.v1",
        required_rubric_ids=("pcf.scope2_method_support.rubric.v1",),
        description="Opens a semantic judgment for Scope 2 method support.",
        evaluator_id="pcf.scope2_method_support.evaluator",
        implementation_version="2026.2",
    )
    rubric = SemanticRubric(
        rubric_id="pcf.scope2_method_support.rubric.v1",
        acceptable_verdicts=("supports", "refutes", "ambiguous"),
        required_verdict="supports",
        description="Determines whether a cited span supports the method.",
    )
    changed_rubric = SemanticRubric(
        rubric_id="pcf.scope2_method_support.rubric.v1",
        acceptable_verdicts=("supports", "refutes"),
        required_verdict="supports",
        description="Determines whether a cited span supports the method.",
    )

    rule_fingerprint = rule_family_declaration_fingerprint(rule)
    rubric_fingerprint = semantic_rubric_declaration_fingerprint(rubric)

    assert rule_fingerprint.dependency_kind == "rule_family"
    assert rule_fingerprint.dependency_id == "pcf.scope2_method_support.v1"
    assert rule_fingerprint != rule_family_declaration_fingerprint(changed_rule)
    assert rule_fingerprint != rule_family_declaration_fingerprint(
        changed_rule_evaluator
    )
    assert rubric_fingerprint.dependency_kind == "semantic_rubric"
    assert rubric_fingerprint.dependency_id == "pcf.scope2_method_support.rubric.v1"
    assert rubric_fingerprint != semantic_rubric_declaration_fingerprint(
        changed_rubric
    )


def test_domain_pack_declaration_fingerprint_pins_domain_policy_manifest():
    domain = DomainPack(
        domain_id="canonical-pcf",
        version="2026.1",
        rule_families=(
            RuleFamily(
                rule_id="pcf.scope2_method_support.v1",
                required_rubric_ids=("pcf.scope2_method_support.rubric.v1",),
            ),
        ),
        rubrics=(
            SemanticRubric(
                rubric_id="pcf.scope2_method_support.rubric.v1",
                acceptable_verdicts=("supports", "refutes", "ambiguous"),
            ),
        ),
        retrieval_query_policies=(
            RetrievalQueryPolicy(
                policy_id="pcf-canonical-retrieval-query-policy-v1",
                rules=(
                    RetrievalQueryRule(
                        rule_id="pcf-electricity-factor-query-v1",
                        formula_id="pcf.electricity_factor_multiplication.v1",
                        lens="factor",
                        reference_type="emission_factor",
                        text_template="{geography} grid electricity factor",
                    ),
                ),
            ),
        ),
    )
    same_domain = DomainPack(
        domain_id="canonical-pcf",
        version="2026.1",
        rule_families=domain.rule_families,
        rubrics=domain.rubrics,
        retrieval_query_policies=domain.retrieval_query_policies,
    )
    changed_domain = DomainPack(
        domain_id="canonical-pcf",
        version="2026.2",
        rule_families=domain.rule_families,
        rubrics=domain.rubrics,
        retrieval_query_policies=domain.retrieval_query_policies,
    )

    fingerprint = domain_pack_declaration_fingerprint(domain)

    assert fingerprint.dependency_kind == "domain_pack"
    assert fingerprint.dependency_id == "domain_pack:canonical-pcf:2026.1"
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == domain_pack_declaration_fingerprint(same_domain)
    assert fingerprint != domain_pack_declaration_fingerprint(changed_domain)
