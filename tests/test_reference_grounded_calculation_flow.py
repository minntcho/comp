from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CompileReport,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    apply_calculation_result,
    calculate_derived_claim,
    resolve_reference_grounded_calculation,
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


def _missing_binding():
    return ReferenceBinding(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.missing",
        reference_type="emission_factor",
    )


def _catalog(*, ambiguous=False):
    extra = ()
    if ambiguous:
        extra = (
            ReferenceRecord(
                reference_id="factor.kr_grid.alt.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024 alternate",),
                aliases=("korea electricity grid factor alternate",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                    ("factor_value", 0.0005),
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
                witness_ids=("ref-factor-row-18",),
            ),
        )
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024",),
                aliases=("korea electricity grid factor",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                    ("factor_value", 0.0004),
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
                witness_ids=("ref-factor-row-17",),
            ),
            *extra,
        )
    )


def _criteria():
    return ReferenceSelectionCriteria(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_type="emission_factor",
        selector_rule_id="ghg.factor_selector.v1",
        required_attributes=(
            ("concept_id", "concept.electricity_consumption"),
            ("geography", "KR"),
            ("valid_period", "2024"),
            ("method", "location_based"),
        ),
    )


def _blocked_report():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_missing_binding(),
        catalog=ReferenceCatalog(records=()),
        formula=_formula(),
    )
    return apply_calculation_result(
        CompileReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )


def test_reference_grounded_calculation_flow_searches_binds_and_retries():
    resolved = resolve_reference_grounded_calculation(
        _blocked_report(),
        _catalog(),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        criteria=_criteria(),
        input_claim=_input(),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert resolved.status == "accepted"
    assert resolved.obligations == ()
    assert [item.kind for item in resolved.resolved_obligations] == [
        "reference_search_required",
        "calculation_blocked",
    ]
    assert [candidate.reference_id for candidate in resolved.reference_candidates] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert [binding.reference_id for binding in resolved.reference_bindings] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert len(resolved.derived_claims) == 1
    assert resolved.derived_claims[0].value == 0.48
    assert resolved.can_project_public_row is False


def test_reference_grounded_calculation_flow_stops_when_search_has_no_candidates():
    resolved = resolve_reference_grounded_calculation(
        _blocked_report(),
        _catalog(),
        query_for_obligation=lambda obligation: "diesel combustion",
        criteria=_criteria(),
        input_claim=_input(),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert resolved.status == "blocked"
    assert resolved.reference_candidates == ()
    assert resolved.reference_bindings == ()
    assert resolved.derived_claims == ()
    assert [item.kind for item in resolved.obligations] == [
        "calculation_blocked",
        "reference_search_required",
    ]


def test_reference_grounded_calculation_flow_exposes_ambiguous_selection():
    resolved = resolve_reference_grounded_calculation(
        _blocked_report(),
        _catalog(ambiguous=True),
        query_for_obligation=lambda obligation: "korea electricity grid factor",
        criteria=_criteria(),
        input_claim=_input(),
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert resolved.status == "blocked"
    assert resolved.reference_bindings == ()
    assert resolved.derived_claims == ()
    assert [item.kind for item in resolved.obligations] == [
        "calculation_blocked",
        "reference_selection_required",
    ]
    assert resolved.obligations[1].reason == "ambiguous"
