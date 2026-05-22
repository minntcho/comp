from __future__ import annotations

from comp import PublicOutputSpec, SubjectRef, build_public_output
from comp.compiler_tool import (
    ReferenceCatalogSnapshot,
    CanonicalReference,
    apply_reference_selection,
    calculation_formula_declaration_fingerprint,
    domain_pack_declaration_fingerprint,
    evidence_ref_fingerprint,
    plan_calculation_resolution,
    prepare_commit,
    profile_declaration_fingerprint,
    profile_lock_envelope_body,
    reference_catalog_snapshot_fingerprint,
    reference_query_for_obligation_from_profile_policy,
    reference_record_fingerprint,
    resolve_reference_retrieval_obligations,
    resolver_tasks_from_report,
    retry_blocked_calculation,
)
from tests.domain_scenarios.canonical_working_loop.expected import (
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
)
from tests.domain_scenarios.canonical_working_loop.fixtures import (
    OUTPUT_CLAIM_ID,
    PROFILE_ID,
    PUBLIC_ROW_ID,
    RAW_EVIDENCE,
    SCENARIO_ID,
    SUBJECT_ID,
    catalog,
    compile_raw_evidence,
    criteria,
    formula,
    input_claim_from_report,
    open_calculation_obligation,
    profile,
    projection_source,
    reference_resolver,
    retrieval_query_context,
)
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


RESOLVER_STEPS = (
    "raw_text_fixture",
    "deterministic_extractor_stub",
    "compiler_tool.compile_interpretation",
    "open_calculation_obligation",
    "plan_calculation_resolution",
    "resolver_tasks_from_report",
    "profile_active_retrieval_policy",
    "resolver_task_to_reference_query",
    "reference_retrieval:embedding_stub:factor",
    "deterministic_reference_selection",
    "retry_calculation",
    "prepare_commit",
    "receipt_gated_projection",
)


SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Canonical raw text PCF working loop",
    run=lambda: run_canonical_working_loop_scenario(),
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=EXPECTED_RESOLVED_OBLIGATION_KINDS,
        required_reference_candidate_ids=EXPECTED_REFERENCE_CANDIDATE_IDS,
        required_reference_binding_ids=("bind-canonical-electricity-factor",),
        required_derived_claim_ids=("canonical-raw:co2e_kg",),
        required_receipt_reference_binding_ids=("bind-canonical-electricity-factor",),
        required_receipt_derived_claim_ids=("canonical-raw:co2e_kg",),
        required_receipt_calculation_trace_ids=("trace:canonical-raw:co2e_kg",),
        required_receipt_formula_ids=("pcf.electricity_factor_multiplication.v1",),
    ),
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="tests/domain_scenarios/canonical_working_loop/fixtures.py",
        ),
    ),
)


def run_canonical_working_loop_scenario() -> DomainScenarioResult:
    scenario_profile = profile()
    compiled_report = compile_raw_evidence(RAW_EVIDENCE)
    blocked_report = open_calculation_obligation(compiled_report)
    planned_report = plan_calculation_resolution(blocked_report)
    resolver_tasks = resolver_tasks_from_report(planned_report)
    retrieval_report = resolve_reference_retrieval_obligations(
        planned_report,
        reference_resolver(),
        query_for_obligation=reference_query_for_obligation_from_profile_policy(
            resolver_tasks,
            profile=scenario_profile,
            context=retrieval_query_context(compiled_report),
        ),
    )
    selected_report = apply_reference_selection(
        retrieval_report,
        catalog(),
        criteria=criteria(),
        field=formula().output_field,
    )
    binding = _binding_for(
        selected_report.canonical_references,
        "bind-canonical-electricity-factor",
    )
    resolved_report = selected_report
    if binding is not None:
        resolved_report = retry_blocked_calculation(
            selected_report,
            catalog(),
            input_claim=input_claim_from_report(compiled_report),
            reference_binding=binding,
            formula=formula(),
            output_claim_id=OUTPUT_CLAIM_ID,
        )
    preparation = prepare_commit(
        resolved_report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id="canonical-pcf-public-row",
        profile_id=scenario_profile.profile_id,
        dependency_fingerprints=_dependency_fingerprints(
            scenario_profile,
            resolved_report,
            binding,
        ),
    )
    projection = None
    if preparation.receipt is not None:
        projection = build_public_output(
            projection_source(resolved_report),
            PublicOutputSpec(
                "canonical-pcf-public-row",
                ("electricity_kwh", "reporting_year", "co2e_kg"),
            ),
            receipt=preparation.receipt,
        )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=resolved_report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
        dependency_artifact_bodies={
            ("compiler_profile", scenario_profile.profile_id): (
                profile_lock_envelope_body(scenario_profile)
            ),
        },
    )


def _dependency_fingerprints(
    scenario_profile,
    report,
    binding: CanonicalReference | None,
):
    fingerprints = [
        profile_declaration_fingerprint(scenario_profile),
        *(
            domain_pack_declaration_fingerprint(domain)
            for domain in scenario_profile.domain_packs
        ),
        calculation_formula_declaration_fingerprint(formula()),
        *tuple(
            evidence_ref_fingerprint(witness)
            for witness in report.evidence_refs
            if witness.witness_id in _checked_claim_witness_ids(report)
        ),
    ]
    if binding is not None:
        record_fingerprint = reference_record_fingerprint(
            catalog().get(binding.reference_id)
        )
        fingerprints.append(
            reference_catalog_snapshot_fingerprint(
                ReferenceCatalogSnapshot.from_catalog(
                    catalog(),
                    catalog_id="pcf-reference-catalog",
                    catalog_version="pcf-reference-catalog-v1",
                    selected_reference_ids=(binding.reference_id,),
                )
            )
        )
        fingerprints.append(record_fingerprint)
    return tuple(fingerprints)


def _checked_claim_witness_ids(report) -> set[str]:
    return {claim.witness_id for claim in report.checked_claims}


def _binding_for(
    bindings: tuple[CanonicalReference, ...],
    binding_id: str,
) -> CanonicalReference | None:
    for binding in reversed(bindings):
        if binding.binding_id == binding_id:
            return binding
    return None


__all__ = ["SCENARIO", "run_canonical_working_loop_scenario"]
