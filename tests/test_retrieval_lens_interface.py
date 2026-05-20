import pytest

from comp.compiler_tool import (
    EmbeddingResolverStub,
    ReferenceCatalog,
    ReferenceIndexEntry,
    ReferenceQuery,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    select_reference_binding,
)


def _entries():
    return (
        ReferenceIndexEntry(
            entry_id="idx-factor-kr-grid-2024",
            reference_id="factor.kr_grid.2024.location_based",
            reference_type="emission_factor",
            lens="factor",
            text="Korea grid electricity factor 2024 location based",
            reference_db_version="refdb-fixture-v1",
            index_version="embedding-stub-v1",
            embedding_model_id="stub-embedding-model",
            source="factor-catalog",
            witness_ids=("factor-row-2024",),
        ),
        ReferenceIndexEntry(
            entry_id="idx-rubric-scope2-method",
            reference_id="rubric.scope2_method_support.v1",
            reference_type="semantic_rubric",
            lens="rubric",
            text="Scope 2 market based method support rubric",
            reference_db_version="refdb-fixture-v1",
            index_version="embedding-stub-v1",
        ),
    )


def test_embedding_resolver_stub_returns_candidate_only_reference_candidates():
    resolver = EmbeddingResolverStub(entries=_entries())

    candidates = resolver.search(
        ReferenceQuery(
            query_id="q-factor",
            text="Korea electricity factor",
            lens="factor",
            reference_type="emission_factor",
            source_artifact_ids=("obl-reference-search",),
        )
    )

    assert [candidate.reference_id for candidate in candidates] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert candidates[0].candidate_id == (
        "embedding_stub:factor:idx-factor-kr-grid-2024"
    )
    assert candidates[0].retrieval_method == "embedding_stub:factor"
    assert candidates[0].retrieval_score is not None
    assert candidates[0].authority == "candidate_only"
    assert candidates[0].can_authorize_calculation is False
    assert candidates[0].source == "factor-catalog"
    assert candidates[0].witness_ids == ("factor-row-2024",)


def test_retrieval_lens_and_reference_type_filter_candidate_space():
    resolver = EmbeddingResolverStub(entries=_entries())

    rubric_candidates = resolver.search(
        ReferenceQuery(
            query_id="q-rubric",
            text="market based method support",
            lens="rubric",
        )
    )
    mismatched_type_candidates = resolver.search(
        ReferenceQuery(
            query_id="q-factor-as-rubric",
            text="Korea electricity factor",
            lens="factor",
            reference_type="semantic_rubric",
        )
    )

    assert [candidate.reference_id for candidate in rubric_candidates] == [
        "rubric.scope2_method_support.v1"
    ]
    assert mismatched_type_candidates == ()


def test_top_ranked_retrieval_candidate_still_requires_deterministic_selection():
    resolver = EmbeddingResolverStub(
        entries=(
            ReferenceIndexEntry(
                entry_id="idx-factor-kr-grid-2023",
                reference_id="factor.kr_grid.2023.location_based",
                reference_type="emission_factor",
                lens="factor",
                text="Korea grid electricity factor 2023 location based",
                reference_db_version="refdb-fixture-v1",
                index_version="embedding-stub-v1",
            ),
        )
    )
    candidates = resolver.search(
        ReferenceQuery(
            query_id="q-factor",
            text="Korea grid electricity factor",
            lens="factor",
            reference_type="emission_factor",
        )
    )
    catalog = ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2023.location_based",
                reference_type="emission_factor",
                labels=("Korea grid electricity factor 2023",),
                attributes=(("valid_period", "2023"),),
            ),
        )
    )

    result = select_reference_binding(
        candidates=candidates,
        catalog=catalog,
        criteria=ReferenceSelectionCriteria(
            binding_id="bind-factor",
            claim_id="claim-electricity",
            reference_type="emission_factor",
            selector_rule_id="pcf.factor_selector.v1",
            required_attributes=(("valid_period", "2024"),),
        ),
    )

    assert candidates[0].can_authorize_calculation is False
    assert result.status == "no_match"
    assert result.binding is None
    assert result.rejected_candidates[0].reason == "attribute_mismatch:valid_period"


def test_reference_query_rejects_unknown_lens():
    with pytest.raises(ValueError, match="unknown retrieval lens"):
        ReferenceQuery(
            query_id="q-unknown",
            text="Korea electricity factor",
            lens="everything",
        )
