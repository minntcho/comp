from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    ValidationReport,
    CanonicalReference,
    ReferenceCatalog,
    ReferenceRecord,
    apply_calculation_result,
    calculate_derived_claim,
    retry_blocked_calculation,
)


def _formula():
    return CalculationFormula(
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_field="co2e_emission",
        output_unit="tCO2e",
    )


def _input():
    return CalculationInput(
        claim_id="hyp-1:amount",
        field="amount",
        value=1200,
        unit="kWh",
    )


def _binding(reference_id):
    return CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id=reference_id,
        reference_type="emission_factor",
        selected_candidate_id="cand-factor",
        selector_rule_id="ghg.factor_selector.v1",
    )


def _empty_catalog():
    return ReferenceCatalog(records=())


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


def _blocked_unknown_reference_report():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_binding("factor.missing"),
        catalog=_empty_catalog(),
        formula=_formula(),
    )
    return apply_calculation_result(
        ValidationReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )


def test_retry_blocked_calculation_resolves_old_obligation_and_adds_derived_claim():
    report = _blocked_unknown_reference_report()
    old_obligation = report.obligations[0]

    updated = retry_blocked_calculation(
        report,
        _catalog(),
        input_claim=_input(),
        reference_binding=_binding("factor.kr_grid.2024.location_based"),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert updated.status == "accepted"
    assert updated.obligations == ()
    assert updated.resolved_obligations == (old_obligation,)
    assert len(updated.derived_claims) == 1
    derived = updated.derived_claims[0]
    assert derived.claim_id == "hyp-1:co2e_emission"
    assert derived.value == 0.48
    assert derived.unit == "tCO2e"
    assert derived.trace.reference_binding_ids == ("bind-amount-factor",)
    assert updated.can_build_public_output is False


def test_retry_blocked_calculation_is_idempotent_after_success():
    report = _blocked_unknown_reference_report()

    once = retry_blocked_calculation(
        report,
        _catalog(),
        input_claim=_input(),
        reference_binding=_binding("factor.kr_grid.2024.location_based"),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )
    twice = retry_blocked_calculation(
        once,
        _catalog(),
        input_claim=_input(),
        reference_binding=_binding("factor.kr_grid.2024.location_based"),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert twice.derived_claims == once.derived_claims
    assert twice.resolved_obligations == once.resolved_obligations
    assert twice.obligations == once.obligations


def test_retry_blocked_calculation_keeps_obligation_open_when_still_blocked():
    report = _blocked_unknown_reference_report()

    updated = retry_blocked_calculation(
        report,
        _empty_catalog(),
        input_claim=_input(),
        reference_binding=_binding("factor.missing"),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert updated.derived_claims == ()
    assert updated.resolved_obligations == ()
    assert updated.obligations == report.obligations
