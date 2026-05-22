import pytest

from comp.compiler_tool import (
    CalculationRequirement,
    ValidationReport,
    CompilerProfile,
    DomainPack,
    EmbeddingResolverStub,
    ValidationRequirement,
    ProfileValidationError,
    ReferenceIndexEntry,
    ReferenceQuery,
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    resolver_tasks_from_report,
    reference_query_for_obligation_from_resolver_tasks,
    reference_query_for_obligation_from_profile_policy,
    reference_query_for_obligation_from_policy,
    reference_query_from_resolver_task,
    resolve_reference_retrieval_obligations,
)


def _reference_search_obligation() -> ValidationRequirement:
    return ValidationRequirement(
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
        ValidationReport(status="blocked", validation_requirements=(_reference_search_obligation(),))
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
        ValidationReport(
            status="review_required",
            validation_requirements=(
                ValidationRequirement(
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
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
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

    assert [candidate.reference_id for candidate in resolved.reference_options] == [
        "factor.kr_grid.2024.location_based"
    ]
    assert resolved.reference_options[0].authority == "candidate_only"
    assert resolved.validation_requirements == ()
    assert resolved.resolved_validation_requirements == (_reference_search_obligation(),)
    assert resolved.canonical_references == ()
    assert resolved.calculated_claims == ()


def test_reference_retrieval_resolution_recomputes_status_after_resolving_only_blocker():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
    )

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_resolver_tasks(
            resolver_tasks_from_report(report),
            query_texts={
                "resolve:formula-v1:claim-co2e:reference_search_required": (
                    "Korea grid electricity factor 2024"
                )
            },
            lens="factor",
            reference_type="emission_factor",
        ),
    )

    assert resolved.validation_requirements == ()
    assert resolved.status == "accepted"


def test_reference_query_builder_from_tasks_leaves_missing_query_open():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
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


def test_retrieval_query_policy_renders_reference_query_from_task_payload_and_context():
    task = resolver_tasks_from_report(
        ValidationReport(status="blocked", validation_requirements=(_reference_search_obligation(),))
    )[0]
    policy = RetrievalQueryPolicy(
        policy_id="pcf-retrieval-policy-v1",
        rules=(
            RetrievalQueryRule(
                rule_id="pcf-electricity-factor-query-v1",
                formula_id="formula-v1",
                lens="factor",
                reference_type="emission_factor",
                text_template="{geography} grid electricity factor {reporting_year}",
            ),
        ),
    )

    query = reference_query_for_obligation_from_policy(
        (task,),
        policy=policy,
        context={"geography": "Korea", "reporting_year": 2024},
    )(_reference_search_obligation())

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


def test_retrieval_query_policy_leaves_obligation_open_without_matching_rule():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
    )
    policy = RetrievalQueryPolicy(
        policy_id="pcf-retrieval-policy-v1",
        rules=(
            RetrievalQueryRule(
                rule_id="other-formula-query-v1",
                formula_id="other-formula",
                lens="factor",
                reference_type="emission_factor",
                text_template="{geography} grid electricity factor {reporting_year}",
            ),
        ),
    )

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_policy(
            resolver_tasks_from_report(report),
            policy=policy,
            context={"geography": "Korea", "reporting_year": 2024},
        ),
    )

    assert resolved == report


def test_retrieval_query_policy_leaves_obligation_open_without_required_context():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
    )
    policy = RetrievalQueryPolicy(
        policy_id="pcf-retrieval-policy-v1",
        rules=(
            RetrievalQueryRule(
                rule_id="pcf-electricity-factor-query-v1",
                formula_id="formula-v1",
                lens="factor",
                reference_type="emission_factor",
                text_template="{geography} grid electricity factor {reporting_year}",
            ),
        ),
    )

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_policy(
            resolver_tasks_from_report(report),
            policy=policy,
            context={"geography": "Korea"},
        ),
    )

    assert resolved == report


def test_profile_pinned_retrieval_policy_feeds_query_builder():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
    )
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            DomainPack(
                domain_id="fixture",
                version="2026.1",
                retrieval_query_policies=(
                    RetrievalQueryPolicy(
                        policy_id="fixture.inactive-retrieval-policy.v1",
                        rules=(),
                    ),
                    RetrievalQueryPolicy(
                        policy_id="fixture.active-retrieval-policy.v1",
                        rules=(
                            RetrievalQueryRule(
                                rule_id="fixture.active-factor-query.v1",
                                formula_id="formula-v1",
                                lens="factor",
                                reference_type="emission_factor",
                                text_template=(
                                    "{geography} grid electricity factor "
                                    "{reporting_year}"
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
        active_retrieval_policy_ids=("fixture.active-retrieval-policy.v1",),
    )

    resolved = resolve_reference_retrieval_obligations(
        report,
        _resolver(),
        query_for_obligation=reference_query_for_obligation_from_profile_policy(
            resolver_tasks_from_report(report),
            profile=profile,
            context={"geography": "Korea", "reporting_year": 2024},
        ),
    )

    assert [candidate.reference_id for candidate in resolved.reference_options] == [
        "factor.kr_grid.2024.location_based"
    ]


def test_profile_retrieval_query_builder_rejects_inactive_policy_id():
    report = ValidationReport(
        status="blocked",
        validation_requirements=(_reference_search_obligation(),),
    )
    profile = CompilerProfile(
        profile_id="fixture-profile",
        domain_packs=(
            DomainPack(
                domain_id="fixture",
                version="2026.1",
                retrieval_query_policies=(
                    RetrievalQueryPolicy(
                        policy_id="fixture.inactive-retrieval-policy.v1",
                        rules=(),
                    ),
                ),
            ),
        ),
        active_retrieval_policy_ids=(),
    )

    with pytest.raises(ProfileValidationError, match="inactive retrieval policy"):
        reference_query_for_obligation_from_profile_policy(
            resolver_tasks_from_report(report),
            profile=profile,
            policy_id="fixture.inactive-retrieval-policy.v1",
            context={"geography": "Korea", "reporting_year": 2024},
        )
