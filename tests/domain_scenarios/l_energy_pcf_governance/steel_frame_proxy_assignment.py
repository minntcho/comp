from __future__ import annotations

from decimal import Decimal

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
    ProofObligation,
    ReferenceBinding,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "l_energy.steel_frame_proxy_assignment.v1"
PROJECTION_ID = "l-energy-steel-frame-proxy-assignment"
PROJECTION_FIELDS = (
    "actor_id",
    "supplier_submission_status",
    "proxy_quality",
    "missing_mass_ton",
    "steel_frame_final_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "steel_frame",
    "supplier_submission_status": "absent",
    "proxy_quality": "Low",
    "missing_mass_ton": 1900,
    "steel_frame_final_emission_tco2e": 4750,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:steel-frame-proxy-assignment"
PUBLIC_ROW_ID = "public-row:steel-frame-proxy-assignment"

FORMULA_ID = "pcf.steel_frame_proxy_assignment.v1"
PROXY_BINDING_ID = "bind:steel-frame:proxy_factor"
MISSING_MASS_CLAIM_ID = "steel-frame:missing_mass_ton"
FINAL_EMISSION_CLAIM_ID = "steel-frame:final_emission_tco2e"
SUPPLIER_ABSENCE_OBLIGATION_ID = (
    "steel-frame:supplier_submission:supplier_submission_absent"
)
PROXY_FACTOR_OBLIGATION_ID = (
    "steel-frame:proxy_factor:missing_supplier_evidence_requires_proxy"
)

ACTOR_ID = "steel_frame"
SUPPLIER_SUBMISSION_STATUS = "absent"
PROXY_QUALITY = "Low"
REQUIRED_LOWER_TIER_INPUT_TON = 6300
VERIFIED_ALPHA_INPUT_TON = 4400
PROXY_FACTOR_TCO2E_PER_TON = Decimal("2.5")

RESOLVER_STEPS = (
    "load_platform_steel_frame_absence_fixture",
    "derive_missing_lower_tier_mass",
    "resolve_supplier_absence_to_proxy_path",
    "bind_proxy_factor",
    "calculate_proxy_emission",
    "prepare_commit",
    "receipt_gated_projection",
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
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
    ),
)


def run_steel_frame_proxy_assignment_scenario():
    report = steel_frame_proxy_assignment_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
    )
    projection = None
    if preparation.receipt is not None:
        projection = project_public_row(
            _projection_source(report),
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=preparation.receipt,
        )
    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def steel_frame_proxy_assignment_report() -> CompileReport:
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=_evidence_witnesses(),
            checked_claims=_checked_claims(),
            resolved_obligations=_resolved_obligations(),
            reference_bindings=_reference_bindings(),
            derived_claims=_derived_claims(),
            can_project_public_row=True,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id="source:c-pack-lower-tier-requirement",
            field="required_lower_tier_input_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.c_pack.required_lower_tier_input_ton",
            text="required lower-tier input 6,300 ton",
        ),
        EvidenceWitness(
            witness_id="source:alpha-metal-verified-input",
            field="verified_alpha_input_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.alpha_metal.corrected_submission.target_panel_ton",
            text="Alpha Metal verified input 4,400 ton",
        ),
        EvidenceWitness(
            witness_id="source:steel-frame-submission-absence",
            field="supplier_submission_status",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.steel_frame.submission_status",
            text="Steel Frame supplier submission absent",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "actor_id",
            ACTOR_ID,
            "source:steel-frame-submission-absence",
            "platform_fixture",
        ),
        CheckedClaim(
            "supplier_submission_status",
            SUPPLIER_SUBMISSION_STATUS,
            "source:steel-frame-submission-absence",
            "platform_fixture",
        ),
        CheckedClaim(
            "required_lower_tier_input_ton",
            REQUIRED_LOWER_TIER_INPUT_TON,
            "source:c-pack-lower-tier-requirement",
            "platform_fixture",
        ),
        CheckedClaim(
            "verified_alpha_input_ton",
            VERIFIED_ALPHA_INPUT_TON,
            "source:alpha-metal-verified-input",
            "platform_fixture",
        ),
        CheckedClaim(
            "proxy_quality",
            PROXY_QUALITY,
            "source:steel-frame-submission-absence",
            "proxy_assignment",
        ),
    )


def _resolved_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="find_source_witness",
            field="steel_frame_supplier_submission",
            reason="supplier_submission_absent",
            obligation_id=SUPPLIER_ABSENCE_OBLIGATION_ID,
        ),
        ProofObligation(
            kind="proxy_factor_required",
            field="steel_frame_proxy_factor",
            reason="missing_supplier_evidence_requires_proxy",
            obligation_id=PROXY_FACTOR_OBLIGATION_ID,
        ),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=PROXY_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.steel_proxy_per_ton",
            reference_type="proxy_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    missing_mass = REQUIRED_LOWER_TIER_INPUT_TON - VERIFIED_ALPHA_INPUT_TON
    proxy_emission = int(Decimal(missing_mass) * PROXY_FACTOR_TCO2E_PER_TON)
    missing_mass_step = CalculationStep(
        step_id="missing-mass-ton",
        operation="subtract",
        input_ids=("required_lower_tier_input_ton", "verified_alpha_input_ton"),
        output_value=missing_mass,
        output_unit="ton",
    )
    proxy_emission_step = CalculationStep(
        step_id="proxy-emission-tco2e",
        operation="multiply",
        input_ids=("missing-mass-ton", PROXY_BINDING_ID),
        output_value=proxy_emission,
        output_unit="tCO2e",
    )
    return (
        DerivedClaim(
            claim_id=MISSING_MASS_CLAIM_ID,
            field="missing_mass_ton",
            value=missing_mass,
            unit="ton",
            origin="proxy_assignment_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{MISSING_MASS_CLAIM_ID}",
                formula_id=FORMULA_ID,
                steps=(missing_mass_step,),
            ),
        ),
        DerivedClaim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="steel_frame_final_emission_tco2e",
            value=proxy_emission,
            unit="tCO2e",
            origin="proxy_assignment_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{FINAL_EMISSION_CLAIM_ID}",
                formula_id=FORMULA_ID,
                input_claim_ids=(MISSING_MASS_CLAIM_ID,),
                reference_binding_ids=(PROXY_BINDING_ID,),
                steps=(missing_mass_step, proxy_emission_step),
            ),
        ),
    )


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


STEEL_FRAME_PROXY_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Steel Frame proxy assignment",
    run=run_steel_frame_proxy_assignment_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=(
            "find_source_witness",
            "proxy_factor_required",
        ),
        required_reference_binding_ids=(PROXY_BINDING_ID,),
        required_derived_claim_ids=(MISSING_MASS_CLAIM_ID, FINAL_EMISSION_CLAIM_ID),
        required_receipt_reference_binding_ids=(PROXY_BINDING_ID,),
        required_receipt_derived_claim_ids=(
            MISSING_MASS_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{MISSING_MASS_CLAIM_ID}",
            f"trace:{FINAL_EMISSION_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "PROXY_BINDING_ID",
    "SCENARIO_ID",
    "STEEL_FRAME_PROXY_SCENARIO",
    "SUPPLIER_ABSENCE_OBLIGATION_ID",
    "run_steel_frame_proxy_assignment_scenario",
    "steel_frame_proxy_assignment_report",
]
