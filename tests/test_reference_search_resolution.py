from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    ValidationReport,
    CanonicalReference,
    ReferenceCatalog,
    ReferenceRecord,
    apply_calculation_result,
    calculate_derived_claim,
    plan_calculation_resolution,
    resolve_reference_search_obligations,
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


def _binding(reference_id="factor.missing"):
    return CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id=reference_id,
        reference_type="emission_factor",
    )


def _empty_catalog():
    return ReferenceCatalog(records=())


def _catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024",),
                aliases=("korea electricity grid factor",),
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


def _planned_unknown_reference_report():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_binding(),
        catalog=_empty_catalog(),
        formula=_formula(),
    )
    blocked = apply_calculation_result(
        ValidationReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )
    return plan_calculation_resolution(blocked)


def test_reference_search_resolution_adds_candidates_and_resolves_followup():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_search_obligations(
        planned,
        _catalog(),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        reference_type="emission_factor",
    )

    assert resolved.status == "blocked"
    assert resolved.can_build_public_output is False
    assert [candidate.reference_id for candidate in resolved.reference_candidates] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert resolved.reference_candidates[0].authority == "candidate_only"
    assert resolved.reference_candidates[0].source == "tiny-fixture"
    assert resolved.reference_candidates[0].witness_ids == ("ref-factor-row-17",)
    assert [obligation.kind for obligation in resolved.obligations] == [
        "calculation_blocked"
    ]
    assert [obligation.kind for obligation in resolved.resolved_obligations] == [
        "reference_search_required"
    ]


def test_reference_search_resolution_recomputes_status_after_resolving_only_blocker():
    obligation = _planned_unknown_reference_report().obligations[1]
    report = ValidationReport(status="blocked", obligations=(obligation,))

    resolved = resolve_reference_search_obligations(
        report,
        _catalog(),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        reference_type="emission_factor",
    )

    assert resolved.obligations == ()
    assert resolved.status == "accepted"


def test_reference_search_resolution_leaves_followup_open_without_query():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_search_obligations(
        planned,
        _catalog(),
        query_for_obligation=lambda obligation: None,
        reference_type="emission_factor",
    )

    assert resolved == planned


def test_reference_search_resolution_leaves_followup_open_without_candidates():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_search_obligations(
        planned,
        _catalog(),
        query_for_obligation=lambda obligation: "diesel combustion",
        reference_type="emission_factor",
    )

    assert resolved == planned


def test_reference_search_resolution_is_idempotent():
    planned = _planned_unknown_reference_report()

    once = resolve_reference_search_obligations(
        planned,
        _catalog(),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        reference_type="emission_factor",
    )
    twice = resolve_reference_search_obligations(
        once,
        _catalog(),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        reference_type="emission_factor",
    )

    assert twice.reference_candidates == once.reference_candidates
    assert twice.resolved_obligations == once.resolved_obligations
    assert twice.obligations == once.obligations
