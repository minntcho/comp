from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CompileReport,
    ProofObligation,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    apply_calculation_result,
    calculate_derived_claim,
    plan_calculation_resolution,
)


def _formula():
    return CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit="tCO2e",
    )


def _input(unit="kWh"):
    return CalculationInput(
        claim_id="hyp-1:amount",
        field="amount",
        value=1200,
        unit=unit,
    )


def _binding(reference_id="factor.kr_grid.2024.location_based"):
    return ReferenceBinding(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id=reference_id,
        reference_type="emission_factor",
    )


def _catalog(*, include_factor_value=True):
    attributes = [
        ("input_unit", "kWh"),
        ("output_unit", "tCO2e"),
    ]
    if include_factor_value:
        attributes.insert(0, ("factor_value", 0.0004))
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                attributes=tuple(attributes),
            ),
        )
    )


def _blocked_report(*, catalog=None, binding=None, input_claim=None):
    calculation = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=input_claim or _input(),
        reference_binding=binding or _binding(),
        catalog=catalog or _catalog(),
        formula=_formula(),
    )
    return apply_calculation_result(
        CompileReport(status="accepted"),
        calculation,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )


def test_unknown_reference_opens_reference_search_obligation():
    report = _blocked_report(binding=_binding(reference_id="factor.missing"))

    planned = plan_calculation_resolution(report)

    assert planned.status == "blocked"
    assert planned.obligations[0].kind == "calculation_blocked"
    follow_up = planned.obligations[1]
    assert follow_up == ProofObligation(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        obligation_id=(
            "resolve:ghg.electricity_factor_multiplication.v1:"
            "hyp-1:co2e_emission:reference_search_required"
        ),
        claim_id="hyp-1:co2e_emission",
        blocking=True,
        calculation_requirement=report.obligations[0].calculation_requirement,
    )


def test_missing_factor_value_opens_reference_context_obligation():
    report = _blocked_report(catalog=_catalog(include_factor_value=False))

    planned = plan_calculation_resolution(report)

    follow_up = planned.obligations[1]
    assert follow_up.kind == "reference_context_required"
    assert follow_up.reason == "missing_factor_value"
    assert follow_up.calculation_requirement is not None
    assert follow_up.calculation_requirement.missing_attribute == "factor_value"


def test_unit_mismatch_opens_find_context_obligation():
    report = _blocked_report(input_claim=_input(unit="MWh"))

    planned = plan_calculation_resolution(report)

    follow_up = planned.obligations[1]
    assert follow_up.kind == "find_context"
    assert follow_up.reason == "unit_mismatch"
    assert follow_up.calculation_requirement is report.obligations[0].calculation_requirement
    assert follow_up.calculation_requirement.expected_unit == "kWh"
    assert follow_up.calculation_requirement.actual_unit == "MWh"


def test_calculation_resolution_planning_is_idempotent():
    report = _blocked_report(input_claim=_input(unit="MWh"))

    once = plan_calculation_resolution(report)
    twice = plan_calculation_resolution(once)

    assert once.obligations == twice.obligations


def test_report_without_calculation_requirement_is_unchanged():
    report = CompileReport(
        status="blocked",
        obligations=(
            ProofObligation(
                kind="calculation_blocked",
                field="co2e_emission",
                reason="unit_mismatch",
            ),
        ),
    )

    planned = plan_calculation_resolution(report)

    assert planned == report
