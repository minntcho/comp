from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    ValidationReport,
    EmbeddingResolverStub,
    CanonicalReference,
    ReferenceCatalog,
    ReferenceIndexEntry,
    ReferenceQuery,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    apply_calculation_result,
    apply_reference_selection,
    calculate_derived_claim,
    plan_calculation_resolution,
    resolve_reference_retrieval_obligations,
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


def _missing_binding():
    return CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="hyp-1:amount",
        reference_id="factor.missing",
        reference_type="emission_factor",
    )


def _catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                    ("factor_value", 0.0004),
                    ("input_unit", "kWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="factor-catalog",
                witness_ids=("factor-row-2024",),
            ),
        )
    )


def _resolver():
    return EmbeddingResolverStub(
        entries=(
            ReferenceIndexEntry(
                entry_id="idx-factor-kr-grid-2024",
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                lens="factor",
                text="Korea grid electricity factor 2024 location based",
                reference_db_version="refdb-fixture-v1",
                index_version="embedding-stub-v1",
                source="factor-catalog",
                witness_ids=("factor-row-2024",),
            ),
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


def _planned_unknown_reference_report():
    result = calculate_derived_claim(
        output_claim_id="hyp-1:co2e_emission",
        input_claim=_input(),
        reference_binding=_missing_binding(),
        catalog=ReferenceCatalog(records=()),
        formula=_formula(),
    )
    blocked = apply_calculation_result(
        ValidationReport(status="accepted"),
        result,
        output_claim_id="hyp-1:co2e_emission",
        formula=_formula(),
    )
    return plan_calculation_resolution(blocked)


def _query_for_obligation(obligation):
    return ReferenceQuery(
        query_id=f"query:{obligation.obligation_id}",
        text="Korea grid electricity factor",
        lens="factor",
        reference_type="emission_factor",
        source_artifact_ids=(obligation.obligation_id or "reference_search_required",),
    )


def test_retrieval_resolution_adds_candidate_only_candidates_and_resolves_search_obligation():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_retrieval_obligations(
        planned,
        _resolver(),
        query_for_obligation=_query_for_obligation,
    )

    assert resolved.status == "blocked"
    assert resolved.can_build_public_output is False
    assert [candidate.reference_id for candidate in resolved.reference_options] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert resolved.reference_options[0].retrieval_method == "embedding_stub:factor"
    assert resolved.reference_options[0].authority == "candidate_only"
    assert resolved.reference_options[0].can_authorize_calculation is False
    assert resolved.reference_options[0].source == "factor-catalog"
    assert resolved.reference_options[0].witness_ids == ("factor-row-2024",)
    assert [obligation.kind for obligation in resolved.validation_requirements] == [
        "calculation_blocked"
    ]
    assert [obligation.kind for obligation in resolved.resolved_validation_requirements] == [
        "reference_search_required"
    ]
    assert resolved.canonical_references == ()
    assert resolved.calculated_claims == ()


def test_retrieval_resolution_leaves_followup_open_without_query():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_retrieval_obligations(
        planned,
        _resolver(),
        query_for_obligation=lambda obligation: None,
    )

    assert resolved == planned


def test_retrieval_resolution_leaves_followup_open_without_candidates():
    planned = _planned_unknown_reference_report()

    resolved = resolve_reference_retrieval_obligations(
        planned,
        _resolver(),
        query_for_obligation=lambda obligation: ReferenceQuery(
            query_id="q-diesel",
            text="diesel combustion",
            lens="factor",
            reference_type="emission_factor",
        ),
    )

    assert resolved == planned


def test_retrieval_resolution_candidates_can_continue_through_selection_and_retry():
    resolved = resolve_reference_retrieval_obligations(
        _planned_unknown_reference_report(),
        _resolver(),
        query_for_obligation=_query_for_obligation,
    )

    selected = apply_reference_selection(
        resolved,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )
    retried = retry_blocked_calculation(
        selected,
        _catalog(),
        input_claim=_input(),
        reference_binding=selected.canonical_references[0],
        formula=_formula(),
        output_claim_id="hyp-1:co2e_emission",
    )

    assert [binding.reference_id for binding in selected.canonical_references] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert selected.calculated_claims == ()
    assert retried.status == "accepted"
    assert retried.validation_requirements == ()
    assert retried.calculated_claims[0].value == 0.48
    assert retried.can_build_public_output is False
