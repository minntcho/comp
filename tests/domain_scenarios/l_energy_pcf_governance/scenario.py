from __future__ import annotations

from comp import PublicOutputSpec, SubjectRef, build_public_output
from comp.compiler_tool import (
    ValidationReport,
    ReferenceCatalogSnapshot,
    CanonicalReference,
    apply_reference_selection,
    calculation_formula_declaration_fingerprint,
    domain_pack_declaration_fingerprint,
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
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    build_domain_scenario_result,
)
from tests.domain_scenarios.l_energy_pcf_governance.expected import (
    EXPECTED_DERIVED_CLAIM_IDS,
    EXPECTED_FORMULA_IDS,
    EXPECTED_PROJECTION,
    EXPECTED_REFERENCE_CANDIDATE_IDS,
    EXPECTED_REFERENCE_BINDING_IDS,
    EXPECTED_RESOLVED_OBLIGATION_KINDS,
    EXPECTED_SOURCE_REFS,
    EXPECTED_TRACE_IDS,
    SCENARIO_ID,
)
from tests.domain_scenarios.l_energy_pcf_governance.fixtures import (
    ELECTRICITY_BINDING_ID,
    OUTPUT_CLAIM_ID,
    PROFILE_ID,
    PUBLIC_ROW_ID,
    SUBJECT_ID,
    attach_downstream_fixture_artifacts,
    blocked_report,
    criteria,
    formula,
    input_claim,
    profile,
    reference_pack,
    retrieval_query_context,
)
from tests.domain_scenarios.reference_packs import ScenarioReferencePack


RESOLVER_STEPS = (
    "load_platform_expected_receipt_fixture",
    "open_l_energy_own_emission_calculation_obligation",
    "plan_calculation_resolution",
    "resolver_tasks_from_report",
    "profile_active_retrieval_policy",
    "resolver_task_to_reference_query",
    "reference_retrieval:embedding_stub:factor",
    "deterministic_reference_selection",
    "retry_calculation",
    "attach_fixture_downstream_claims",
    "prepare_commit",
    "receipt_gated_projection",
)

PROJECTION_FIELDS = (
    "case_id",
    "total_emission_tco2e",
    "packs",
    "total_energy_gwh",
    "kgco2e_per_pack",
    "kgco2e_per_kwh",
)
PROJECTION_ID = "l-energy-pcf-public-row"


def _contract_dependency_fingerprints():
    return _dependency_fingerprints_for_reference_ids(
        profile(),
        reference_pack(),
        EXPECTED_REFERENCE_CANDIDATE_IDS,
    )


def _dependency_fingerprints_for_reference_ids(
    scenario_profile,
    pack: ScenarioReferencePack,
    reference_ids: tuple[str, ...],
):
    fingerprints = [
        profile_declaration_fingerprint(scenario_profile),
        *(
            domain_pack_declaration_fingerprint(domain)
            for domain in scenario_profile.domain_packs
        ),
        calculation_formula_declaration_fingerprint(formula()),
    ]
    selected_reference_ids = []
    record_fingerprints = []
    seen_reference_ids: set[str] = set()
    for reference_id in reference_ids:
        if reference_id in seen_reference_ids:
            continue
        seen_reference_ids.add(reference_id)
        selected_reference_ids.append(reference_id)
        record_fingerprints.append(
            reference_record_fingerprint(pack.catalog.get(reference_id))
        )
    if selected_reference_ids:
        fingerprints.append(
            reference_catalog_snapshot_fingerprint(
                ReferenceCatalogSnapshot.from_catalog(
                    pack.catalog,
                    catalog_id=pack.pack_id,
                    catalog_version=pack.reference_db_version,
                    selected_reference_ids=tuple(selected_reference_ids),
                )
            )
        )
        fingerprints.extend(record_fingerprints)
    return tuple(fingerprints)


SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="L-Energy PCF Governance",
    run=lambda: run_l_energy_pcf_governance_scenario(),
    source_refs=EXPECTED_SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=EXPECTED_RESOLVED_OBLIGATION_KINDS,
        required_reference_candidate_ids=EXPECTED_REFERENCE_CANDIDATE_IDS,
        required_reference_binding_ids=EXPECTED_REFERENCE_BINDING_IDS,
        required_derived_claim_ids=EXPECTED_DERIVED_CLAIM_IDS,
        required_receipt_reference_binding_ids=EXPECTED_REFERENCE_BINDING_IDS,
        required_receipt_derived_claim_ids=EXPECTED_DERIVED_CLAIM_IDS,
        required_receipt_calculation_trace_ids=EXPECTED_TRACE_IDS,
        required_receipt_formula_ids=EXPECTED_FORMULA_IDS,
        required_dependency_fingerprints=_contract_dependency_fingerprints(),
    ),
)


def run_l_energy_pcf_governance_scenario(
    *,
    reference_pack_override: ScenarioReferencePack | None = None,
) -> DomainScenarioResult:
    pack = reference_pack_override or reference_pack()
    scenario_profile = profile()
    report = _compile_retrieval_backed_report(
        reference_pack_override=pack,
        scenario_profile=scenario_profile,
    )
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
        dependency_fingerprints=_dependency_fingerprints(
            scenario_profile,
            pack,
            report,
        ),
    )
    projection = None
    if preparation.receipt is not None:
        projection = build_public_output(
            _projection_source(report),
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=preparation.receipt,
        )

    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
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


def _projection_source(report) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _compile_retrieval_backed_report(
    *,
    reference_pack_override: ScenarioReferencePack,
    scenario_profile,
) -> ValidationReport:
    pack = reference_pack_override
    opened_report = blocked_report()
    planned_report = plan_calculation_resolution(opened_report)
    resolver_tasks = resolver_tasks_from_report(planned_report)
    retrieval_report = resolve_reference_retrieval_obligations(
        planned_report,
        pack.resolver,
        query_for_obligation=reference_query_for_obligation_from_profile_policy(
            resolver_tasks,
            profile=scenario_profile,
            context=retrieval_query_context(),
        ),
    )
    selected_report = apply_reference_selection(
        retrieval_report,
        pack.catalog,
        criteria=criteria(),
        field=formula().output_field,
    )
    binding = _binding_for(selected_report.reference_bindings, ELECTRICITY_BINDING_ID)
    resolved_report = selected_report
    if binding is not None:
        resolved_report = retry_blocked_calculation(
            selected_report,
            pack.catalog,
            input_claim=input_claim(),
            reference_binding=binding,
            formula=formula(),
            output_claim_id=OUTPUT_CLAIM_ID,
        )
    return attach_downstream_fixture_artifacts(resolved_report)


def _dependency_fingerprints(
    scenario_profile,
    pack: ScenarioReferencePack,
    report: ValidationReport,
):
    return _dependency_fingerprints_for_reference_ids(
        scenario_profile,
        pack,
        tuple(candidate.reference_id for candidate in report.reference_candidates),
    )


def _binding_for(
    bindings: tuple[CanonicalReference, ...],
    binding_id: str,
) -> CanonicalReference | None:
    for binding in reversed(bindings):
        if binding.binding_id == binding_id:
            return binding
    return None


__all__ = ["SCENARIO", "run_l_energy_pcf_governance_scenario"]
