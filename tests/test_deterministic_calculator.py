from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CalculationResult,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    calculate_derived_claim,
)


def _catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024",),
                attributes=(
                    ("factor_value", 0.0004),
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-17",),
            ),
        )
    )


def _binding(reference_id="factor.kr_grid.2024.location_based"):
    return ReferenceBinding(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id=reference_id,
        reference_type="emission_factor",
        selected_candidate_id="cand-factor",
        selector_rule_id="ghg.factor_selector.v1",
        source_witness_ids=("ref-factor-row-17",),
    )


def _input(value=1200, unit="kWh"):
    return CalculationInput(
        claim_id="hyp-1:amount",
        field="amount",
        value=value,
        unit=unit,
    )


def _formula():
    return CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit="tCO2e",
    )


def test_calculator_generates_derived_claim_from_binding_and_formula():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )

    assert isinstance(result, CalculationResult)
    assert result.status == "calculated"
    assert result.reason is None
    assert result.derived_claim is not None
    assert result.derived_claim.claim_id == "hyp-1:co2e_emission"
    assert result.derived_claim.field == "co2e_emission"
    assert result.derived_claim.value == 0.48
    assert result.derived_claim.unit == "tCO2e"
    assert result.derived_claim.formula_id == "ghg.electricity_factor_multiplication.v1"
    assert result.derived_claim.can_authorize_public_projection is False
    assert result.derived_claim.trace.input_claim_ids == ("hyp-1:amount",)
    assert result.derived_claim.trace.reference_binding_ids == ("bind-amount-factor",)
    assert result.derived_claim.trace.steps[0].operation == "multiply"
    assert result.derived_claim.trace.steps[0].input_ids == (
        "hyp-1:amount",
        "bind-amount-factor",
    )
    assert result.derived_claim.trace.steps[0].output_value == 0.48
    assert result.derived_claim.trace.steps[0].output_unit == "tCO2e"


def test_calculator_blocks_unit_mismatch():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(unit="MWh"),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=_formula(),
    )

    assert result.status == "blocked"
    assert result.reason == "unit_mismatch"
    assert result.derived_claim is None


def test_calculator_blocks_missing_factor_value():
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
        input_claim=_input(),
        reference_binding=_binding(),
        catalog=catalog,
        formula=_formula(),
    )

    assert result.status == "blocked"
    assert result.reason == "missing_factor_value"
    assert result.derived_claim is None


def test_calculator_blocks_output_unit_mismatch():
    formula = CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit="kgCO2e",
    )

    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_binding(),
        catalog=_catalog(),
        formula=formula,
    )

    assert result.status == "blocked"
    assert result.reason == "output_unit_mismatch"
    assert result.derived_claim is None


def test_calculator_blocks_unknown_binding_reference():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_binding(reference_id="factor.missing"),
        catalog=_catalog(),
        formula=_formula(),
    )

    assert result.status == "blocked"
    assert result.reason == "unknown_reference"
    assert result.derived_claim is None
