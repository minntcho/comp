from comp.compiler_tool import (
    ReferenceOption,
    ReferenceCatalog,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    ReferenceSelectionResult,
    select_reference_binding,
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
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-17",),
            ),
            ReferenceRecord(
                reference_id="factor.kr_residual_mix.2024.market_based",
                reference_type="emission_factor",
                labels=("KR residual mix electricity factor 2024",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "market_based"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-18",),
            ),
            ReferenceRecord(
                reference_id="factor.us_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("US grid electricity factor 2024",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "US"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-19",),
            ),
        )
    )


def _candidate(candidate_id, reference_id, score):
    return ReferenceOption(
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


def test_reference_selector_binds_single_deterministic_match():
    result = select_reference_binding(
        candidates=(
            _candidate("cand-market", "factor.kr_residual_mix.2024.market_based", 0.96),
            _candidate("cand-location", "factor.kr_grid.2024.location_based", 0.82),
            _candidate("cand-us", "factor.us_grid.2024.location_based", 0.73),
        ),
        catalog=_catalog(),
        criteria=_criteria(),
    )

    assert isinstance(result, ReferenceSelectionResult)
    assert result.status == "bound"
    assert result.binding is not None
    assert result.binding.reference_id == "factor.kr_grid.2024.location_based"
    assert result.binding.selected_candidate_id == "cand-location"
    assert result.binding.selector_rule_id == "ghg.factor_selector.v1"
    assert result.binding.source_witness_ids == ("ref-factor-row-17",)
    assert result.binding.rejected_candidates == result.rejected_candidates
    assert result.binding.can_authorize_calculation is True
    assert [(item.candidate_id, item.reason) for item in result.rejected_candidates] == [
        ("cand-market", "attribute_mismatch:method"),
        ("cand-us", "attribute_mismatch:geography"),
    ]


def test_reference_selector_does_not_auto_pick_top_score_when_ambiguous():
    result = select_reference_binding(
        candidates=(
            _candidate("cand-a", "factor.kr_grid.2024.location_based", 0.99),
            _candidate("cand-b", "factor.kr_grid.2024.location_based", 0.76),
        ),
        catalog=_catalog(),
        criteria=_criteria(),
    )

    assert result.status == "ambiguous"
    assert result.binding is None
    assert result.accepted_candidate_ids == ("cand-a", "cand-b")
    assert result.rejected_candidates == ()


def test_reference_selector_reports_no_match_and_unknown_references():
    result = select_reference_binding(
        candidates=(
            _candidate("cand-market", "factor.kr_residual_mix.2024.market_based", 0.96),
            _candidate("cand-missing", "factor.missing", 0.95),
        ),
        catalog=_catalog(),
        criteria=_criteria(),
    )

    assert result.status == "no_match"
    assert result.binding is None
    assert result.accepted_candidate_ids == ()
    assert [(item.candidate_id, item.reason) for item in result.rejected_candidates] == [
        ("cand-market", "attribute_mismatch:method"),
        ("cand-missing", "unknown_reference"),
    ]


def test_reference_selector_rejects_reference_type_mismatch():
    result = select_reference_binding(
        candidates=(
            ReferenceOption(
                candidate_id="cand-unit",
                reference_id="unit.kwh",
                reference_type="unit",
                retrieval_method="keyword",
            ),
        ),
        catalog=ReferenceCatalog(
            records=(
                ReferenceRecord(
                    reference_id="unit.kwh",
                    reference_type="unit",
                ),
            )
        ),
        criteria=_criteria(),
    )

    assert result.status == "no_match"
    assert [(item.candidate_id, item.reason) for item in result.rejected_candidates] == [
        ("cand-unit", "reference_type_mismatch"),
    ]
