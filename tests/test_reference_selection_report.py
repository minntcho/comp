from comp.compiler_tool import (
    CompileReport,
    ProofObligation,
    ReferenceCandidate,
    ReferenceCatalog,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    apply_reference_selection,
)


def _catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-17",),
            ),
            ReferenceRecord(
                reference_id="factor.kr_residual_mix.2024.market_based",
                reference_type="emission_factor",
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "market_based"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-18",),
            ),
        )
    )


def _candidate(candidate_id, reference_id, score):
    return ReferenceCandidate(
        candidate_id=candidate_id,
        reference_id=reference_id,
        reference_type="emission_factor",
        retrieval_method="keyword",
        retrieval_score=score,
        source="tiny-fixture",
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


def _selection_obligation(reason="ambiguous"):
    return ProofObligation(
        kind="reference_selection_required",
        field="co2e_emission",
        reason=reason,
        obligation_id="reference_selection:ghg.factor_selector.v1:hyp-1:amount",
        claim_id="hyp-1:amount",
        blocking=True,
    )


def test_reference_selection_adds_binding_and_resolves_matching_obligation():
    obligation = _selection_obligation()
    report = CompileReport(
        status="blocked",
        obligations=(obligation,),
        reference_candidates=(
            _candidate(
                "cand-market",
                "factor.kr_residual_mix.2024.market_based",
                0.96,
            ),
            _candidate(
                "cand-location",
                "factor.kr_grid.2024.location_based",
                0.82,
            ),
        ),
    )

    updated = apply_reference_selection(
        report,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )

    assert updated.status == "accepted"
    assert updated.can_project_public_row is False
    assert updated.obligations == ()
    assert updated.resolved_obligations == (obligation,)
    assert len(updated.reference_bindings) == 1
    binding = updated.reference_bindings[0]
    assert binding.reference_id == "factor.kr_grid.2024.location_based"
    assert binding.selected_candidate_id == "cand-location"
    assert binding.selector_rule_id == "ghg.factor_selector.v1"
    assert binding.source_witness_ids == ("ref-factor-row-17",)
    assert [(item.candidate_id, item.reason) for item in binding.rejected_candidates] == [
        ("cand-market", "attribute_mismatch:method")
    ]


def test_reference_selection_opens_obligation_when_candidates_are_ambiguous():
    report = CompileReport(
        status="accepted",
        reference_candidates=(
            _candidate("cand-a", "factor.kr_grid.2024.location_based", 0.99),
            _candidate("cand-b", "factor.kr_grid.2024.location_based", 0.76),
        ),
    )

    updated = apply_reference_selection(
        report,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )

    assert updated.status == "blocked"
    assert updated.reference_bindings == ()
    assert updated.obligations == (_selection_obligation(reason="ambiguous"),)


def test_reference_selection_opens_obligation_when_no_candidate_matches():
    report = CompileReport(
        status="accepted",
        reference_candidates=(
            _candidate(
                "cand-market",
                "factor.kr_residual_mix.2024.market_based",
                0.96,
            ),
        ),
    )

    updated = apply_reference_selection(
        report,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )

    assert updated.status == "blocked"
    assert updated.reference_bindings == ()
    assert updated.obligations == (_selection_obligation(reason="no_match"),)


def test_reference_selection_report_application_is_idempotent():
    report = CompileReport(
        status="accepted",
        reference_candidates=(
            _candidate("cand-a", "factor.kr_grid.2024.location_based", 0.99),
            _candidate("cand-b", "factor.kr_grid.2024.location_based", 0.76),
        ),
    )

    once = apply_reference_selection(
        report,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )
    twice = apply_reference_selection(
        once,
        _catalog(),
        criteria=_criteria(),
        field="co2e_emission",
    )

    assert twice.obligations == once.obligations
    assert twice.reference_bindings == once.reference_bindings
