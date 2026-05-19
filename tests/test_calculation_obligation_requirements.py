from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CalculationRequirement,
    CompileReport,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    apply_calculation_result,
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
            ),
        )
    )


def _binding(reference_id="factor.kr_grid.2024.location_based"):
    return ReferenceBinding(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id=reference_id,
        reference_type="emission_factor",
    )


def _formula(output_unit="tCO2e"):
    return CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit=output_unit,
    )


def test_blocked_calculation_result_carries_structured_requirement():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=CalculationInput(
            claim_id="hyp-1:amount",
            field="amount",
            value=1200,
            unit="MWh",
        ),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )

    assert result.status == "blocked"
    assert result.requirement == CalculationRequirement(
        reason="unit_mismatch",
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_claim_id="hyp-1:co2e_emission",
        input_claim_id="hyp-1:amount",
        reference_binding_id="bind-amount-factor",
        reference_id="factor.kr_grid.2024.location_based",
        expected_unit="kWh",
        actual_unit="MWh",
    )


def test_blocked_calculation_report_obligation_carries_requirement_payload():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=CalculationInput(
            claim_id="hyp-1:amount",
            field="amount",
            value=1200,
            unit="MWh",
        ),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )

    report = apply_calculation_result(
        CompileReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )

    assert report.obligations[0].calculation_requirement == result.requirement


def test_calculation_requirement_metadata_is_visible_to_judgment_facts():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=CalculationInput(
            claim_id="hyp-1:amount",
            field="amount",
            value=1200,
            unit="MWh",
        ),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )
    report = apply_calculation_result(
        CompileReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )

    facts = compile_report_to_facts(report, SubjectRef("claim", "hyp-1"))

    assert Fact(
        tag="hazard_open",
        subject=SubjectRef("claim", "hyp-1"),
        key="proof_obligation:co2e_emission",
        value="proof_obligation:calculation_blocked:co2e_emission:unit_mismatch",
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


def test_missing_factor_requirement_names_missing_attribute():
    catalog = ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                attributes=(
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
            ),
        )
    )

    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=CalculationInput(
            claim_id="hyp-1:amount",
            field="amount",
            value=1200,
            unit="kWh",
        ),
        reference_binding=_binding(),
        catalog=catalog,
        formula=_formula(),
    )

    assert result.requirement is not None
    assert result.requirement.reason == "missing_factor_value"
    assert result.requirement.missing_attribute == "factor_value"
