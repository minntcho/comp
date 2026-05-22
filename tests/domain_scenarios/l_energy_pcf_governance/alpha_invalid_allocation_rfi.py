from __future__ import annotations

from comp import SubjectRef
from comp.compiler_tool import (
    CheckedClaim,
    ValidationReport,
    EvidenceRef,
    FailedClaim,
    Hazard,
    ValidationRequirement,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "l_energy.alpha_invalid_allocation_rfi.v1"
PROJECTION_ID = "l-energy-alpha-invalid-allocation-rfi"
PROJECTION_FIELDS = ("raw_material_name",)
SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:alpha-metal-invalid-allocation"
PUBLIC_ROW_ID = "public-row:alpha-metal-invalid-allocation-rfi"
RAW_MATERIAL_NAME = "알미늄 판넬"
NORMALIZATION_SUGGESTION = "Aluminum Sheet"
ALLOCATION_METHOD = "revenue_share"
ALLOCATION_SHARE = 0.30
ROLLING_RESIDENCE_OBLIGATION_ID = (
    "alpha-metal:rolling_residence_time:physical_allocation_parameter_required"
)
METHODOLOGICAL_HAZARD_ID = (
    "hazard:methodological_allocation_error:allocation_method:block"
)

RESOLVER_STEPS = (
    "load_platform_alpha_invalid_allocation_fixture",
    "material_normalization_suggestion:proposal_only",
    "deterministic_allocation_method_rule",
    "prepare_commit",
    "projection_blocked",
)

SOURCE_REFS = (
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="docs/e2e/cases/001-l-energy-pcf-governance.md",
    ),
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="docs/e2e/dummy-data-mapping-l-energy-pcf.md",
    ),
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
    ),
)


def run_alpha_invalid_allocation_rfi_scenario():
    report = alpha_invalid_allocation_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
    )
    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=None,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def alpha_invalid_allocation_report() -> ValidationReport:
    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=(
                EvidenceRef(
                    witness_id="source:alpha-metal-initial-submission",
                    field="raw_material_name",
                    source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
                    span="data_setup.alpha_metal.raw_submission.raw_material_name",
                    text=RAW_MATERIAL_NAME,
                ),
            ),
            checked_claims=(
                CheckedClaim(
                    field="raw_material_name",
                    value=RAW_MATERIAL_NAME,
                    witness_id="source:alpha-metal-initial-submission",
                    origin="supplier_submission",
                ),
            ),
            failed_claims=(
                FailedClaim(
                    field="allocation_method",
                    value=ALLOCATION_METHOD,
                    reason="economic_allocation_not_allowed",
                    origin="supplier_submission",
                    witness_id="source:alpha-metal-initial-submission",
                ),
            ),
            validation_requirements=(
                ValidationRequirement(
                    kind="find_context",
                    field="rolling_residence_time",
                    reason="physical_allocation_parameter_required",
                    requirement_id=ROLLING_RESIDENCE_OBLIGATION_ID,
                ),
            ),
            hazards=(
                Hazard(
                    kind="methodological_allocation_error",
                    field="allocation_method",
                    severity="block",
                ),
            ),
            can_build_public_output=False,
        )
    )


ALPHA_INVALID_ALLOCATION_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Alpha Metal invalid allocation RFI",
    run=run_alpha_invalid_allocation_rfi_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        required_open_obligation_ids=(ROLLING_RESIDENCE_OBLIGATION_ID,),
        required_hazard_ids=(METHODOLOGICAL_HAZARD_ID,),
    ),
)


__all__ = [
    "ALLOCATION_METHOD",
    "ALLOCATION_SHARE",
    "ALPHA_INVALID_ALLOCATION_SCENARIO",
    "METHODOLOGICAL_HAZARD_ID",
    "NORMALIZATION_SUGGESTION",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "RAW_MATERIAL_NAME",
    "RESOLVER_STEPS",
    "ROLLING_RESIDENCE_OBLIGATION_ID",
    "SCENARIO_ID",
    "SOURCE_CASE_ID",
    "alpha_invalid_allocation_report",
    "run_alpha_invalid_allocation_rfi_scenario",
]
