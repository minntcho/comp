import pytest

from comp.compiler_tool import (
    CalculationRequirement,
    CompileReport,
    EmbeddingResolverStub,
    ProofObligation,
    ReferenceIndexEntry,
    ReferenceQuery,
    resolver_tasks_from_report,
    reference_query_for_obligation_from_resolver_tasks,
    reference_query_from_resolver_task,
    resolve_reference_retrieval_obligations,
)


def _reference_search_obligation() -> ProofObligation:
    return ProofObligation(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        obligation_id="resolve:formula-v1:claim-co2e:reference_search_required",
        claim_id="claim-co2e",
        calculation_requirement=CalculationRequirement(
            reason="unknown_reference",
            formula_id="formula-v1",
            output_claim_id="claim-co2e",
            input_claim_id="claim-electricity",
            reference_binding_id="bind-electricity-factor",
            reference_id="factor.missing",
        ),
    )


def _resolver() -> EmbeddingResolverStub:
    return EmbeddingResolverStub(
        entries=(
            ReferenceIndexEntry(
                entry_id="idx-factor-kr-grid-2024",
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                lens="factor",
                text="Korea grid electricity factor 2024 location based",
                reference_db_version="refdb-v1",
                index_version="embedding-stub-v1",
            ),
        )
    )


def test_reference_query_from_resolver_task_preserves_task_identity():
    task = resolver_tasks_from_report(
        CompileReport(status="blocked", obligations=(_reference_search_obligation(),))
    )[0]

    query = reference_query_from_resolver_task(
        task,
        text="Korea grid electricity factor 2024",
        lens="factor",
        reference_type="emission_factor",
    )

    assert query == ReferenceQuery(
        query_id=(
            "reference-query:"
            "resolve:formula-v1:claim-co2e:reference_search_required"
        ),
        text="Korea grid electricity factor 2024",
        lens="factor",
        reference_type="emission_factor",
        source_artifact_ids=(
            "resolver-task:resolve:formula-v1:claim-co2e:"
            "reference_search_required",
            "resolve:formula-v1:claim-co2e:reference_search_required",
        ),
    )


def test_reference_query_from_resolver_task_rejects_non_reference_search_task():
    task = resolver_tasks_from_report(
        CompileReport(
            status="review_required",
            obligations=(
                ProofObligation(
                    kind="find_source_witness",
                    field="unit",
                    reason="missing_unit",
                ),
            ),
        )
    )[0]

    with pytest.raises(ValueError, match="reference_search"):
        reference_query_from_resolver_task(
            task,
            text="unit",
            lens="unit",
        )


def test_reference_query_builder_from_tasks_feeds_retrieval_bridge():
    report = CompileReport(
        status="blocked",
        obligations=(_reference_search_obligation(),),
    )
    tasks = resolver_tasks_from_report(report)

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_resolver_tasks(
            tasks,
            query_texts={
                "resolve:formula-v1:claim-co2e:reference_search_required": (
                    "Korea grid electricity factor 2024"
                )
            },
            lens="factor",
            reference_type="emission_factor",
        ),
    )

    assert [candidate.reference_id for candidate in resolved.reference_candidates] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert resolved.reference_candidates[0].authority == "candidate_only"
    assert resolved.obligations == ()
    assert resolved.resolved_obligations == (_reference_search_obligation(),)
    assert resolved.reference_bindings == ()
    assert resolved.derived_claims == ()


def test_reference_query_builder_from_tasks_leaves_missing_query_open():
    report = CompileReport(
        status="blocked",
        obligations=(_reference_search_obligation(),),
    )

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_resolver_tasks(
            resolver_tasks_from_report(report),
            query_texts={},
            lens="factor",
            reference_type="emission_factor",
        ),
    )

    assert resolved == report
