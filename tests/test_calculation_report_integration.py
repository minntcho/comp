from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CalculationRequirement,
    CompileReport,
    ProofObligation,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    apply_calculation_result,
    apply_semantic_judgments,
    calculate_derived_claim,
    compile_report_to_facts,
)
from comp.judgment import Fact, SubjectRef


def _catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                attributes=(
                    ("factor_value", 0.0004),
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
                witness_ids=("ref-factor-row-17",),
            ),
        )
    )


def _binding():
    return ReferenceBinding(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.kr_grid.2024.location_based",
        reference_type="emission_factor",
        selected_candidate_id="cand-factor",
        selector_rule_id="ghg.factor_selector.v1",
        source_witness_ids=("ref-factor-row-17",),
    )


def _input(unit="kWh"):
    return CalculationInput(
        claim_id="hyp-1:amount",
        field="amount",
        value=1200,
        unit=unit,
    )


def _formula():
    return CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit="tCO2e",
    )


def test_successful_calculation_adds_derived_claim_to_report():
    binding = _binding()
    calculation = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=binding,
        catalog=_catalog(),
        formula=_formula(),
    )
    report = CompileReport(status="accepted", reference_bindings=(binding,))

    updated = apply_calculation_result(
        report,
        calculation,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )

    assert updated.status == "accepted"
    assert updated.reference_bindings == (binding,)
    assert updated.derived_claims == (calculation.derived_claim,)
    assert updated.obligations == ()
    assert updated.can_project_public_row is False


def test_blocked_calculation_opens_blocking_obligation_on_report():
    binding = _binding()
    calculation = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(unit="MWh"),
        reference_binding=binding,
        catalog=_catalog(),
        formula=_formula(),
    )
    report = CompileReport(status="accepted", reference_bindings=(binding,))

    updated = apply_calculation_result(
        report,
        calculation,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )

    assert updated.status == "blocked"
    assert updated.reference_bindings == (binding,)
    assert updated.derived_claims == ()
    assert updated.obligations == (
        ProofObligation(
            kind="calculation_blocked",
            field="co2e_emission",
            reason="unit_mismatch",
            obligation_id=(
                "calculation:ghg.electricity_factor_multiplication.v1:"
                "hyp-1:co2e_emission:unit_mismatch"
            ),
            claim_id="hyp-1:co2e_emission",
            blocking=True,
            calculation_requirement=CalculationRequirement(
                reason="unit_mismatch",
                formula_id="ghg.electricity_factor_multiplication.v1",
                output_claim_id="hyp-1:co2e_emission",
                input_claim_id="hyp-1:amount",
                reference_binding_id="bind-amount-factor",
                reference_id="factor.kr_grid.2024.location_based",
                expected_unit="kWh",
                actual_unit="MWh",
            ),
        ),
    )
    assert updated.can_project_public_row is False


def test_calculation_obligation_maps_to_judgment_fact():
    calculation = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(unit="MWh"),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )
    report = apply_calculation_result(
        CompileReport(status="accepted"),
        calculation,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )
    subject = SubjectRef("claim", "hyp-1")

    facts = compile_report_to_facts(report, subject)

    assert Fact(
        tag="hazard_open",
        subject=subject,
        key="proof_obligation:co2e_emission",
        value=(
            "calculation:ghg.electricity_factor_multiplication.v1:"
            "hyp-1:co2e_emission:unit_mismatch"
        ),
        meta=(
            ("kind", "calculation_blocked"),
            ("reason", "unit_mismatch"),
            ("actual_unit", "MWh"),
            ("expected_unit", "kWh"),
            ("formula_id", "ghg.electricity_factor_multiplication.v1"),
            ("input_claim_id", "hyp-1:amount"),
            ("output_claim_id", "hyp-1:co2e_emission"),
            ("reference_binding_id", "bind-amount-factor"),
            ("reference_id", "factor.kr_grid.2024.location_based"),
            ("report_section", "proof_obligation"),
            ("report_status", "blocked"),
        ),
    ) in facts


def test_semantic_application_preserves_open_calculation_obligation_status():
    calculation = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(unit="MWh"),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )
    report = apply_calculation_result(
        CompileReport(status="accepted"),
        calculation,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )

    updated = apply_semantic_judgments(report, ())

    assert updated.status == "blocked"
    assert updated.obligations == report.obligations
