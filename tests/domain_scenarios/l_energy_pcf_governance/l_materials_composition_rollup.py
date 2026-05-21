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
    FailedClaim,
    Hazard,
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


SCENARIO_ID = "l_energy.l_materials_composition_rollup.v1"
PROJECTION_ID = "l-energy-l-materials-composition-rollup"
PROJECTION_FIELDS = (
    "actor_id",
    "material_family",
    "composition_total",
    "l_materials_final_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "l_materials",
    "material_family": "NCM811",
    "composition_total": 1.0,
    "l_materials_final_emission_tco2e": 174375,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:l-materials-composition"
PUBLIC_ROW_ID = "public-row:l-materials-composition-rollup"

FORMULA_ID = "pcf.l_materials_ncm_composition.v1"
COMPOSITION_FACTOR_BINDING_ID = "bind:l-materials:ncm811_composition_factor"
COMPOSITION_TOTAL_CLAIM_ID = "l-materials:composition_total"
FINAL_EMISSION_CLAIM_ID = "l-materials:final_emission_tco2e"
COMPOSITION_TOTAL_OBLIGATION_ID = "l-materials:ncm_composition:shares_sum_to_one"

ACTOR_ID = "l_materials"
MATERIAL_FAMILY = "NCM811"
NI_SHARE = Decimal("0.80")
CO_SHARE = Decimal("0.10")
MN_SHARE = Decimal("0.10")
INVALID_MN_SHARE = Decimal("0.05")
PRODUCTION_TON = 11250
MAPPED_NCM_FACTOR_TCO2E_PER_TON = Decimal("15.5")

RESOLVER_STEPS = (
    "load_platform_l_materials_composition_fixture",
    "validate_ncm_composition_total",
    "bind_ncm811_composition_factor",
    "calculate_composition_rollup",
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


def run_l_materials_composition_rollup_scenario():
    report = l_materials_composition_rollup_report()
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


def l_materials_composition_rollup_report() -> CompileReport:
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


def invalid_l_materials_composition_report() -> CompileReport:
    composition_total = _number(NI_SHARE + CO_SHARE + INVALID_MN_SHARE)
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=_evidence_witnesses(),
            checked_claims=_checked_claims(mn_share=INVALID_MN_SHARE),
            failed_claims=(
                FailedClaim(
                    field="composition_total",
                    value=composition_total,
                    reason="ERR_COMPOSITION_TOTAL",
                    origin="composition_rule",
                    witness_id="source:l-materials-composition",
                ),
            ),
            hazards=(
                Hazard(
                    kind="composition_mapping_error",
                    field="ncm_composition",
                    severity="block",
                ),
            ),
            can_project_public_row=False,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id="source:l-materials-composition",
            field="ncm_composition",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.l_materials.composition",
            text="Ni 80%, Co 10%, Mn 10%",
        ),
        EvidenceWitness(
            witness_id="source:l-materials-production",
            field="production_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.l_materials.production_ton",
            text="11,250 ton",
        ),
        EvidenceWitness(
            witness_id="source:l-materials-ncm-factor",
            field="mapped_ncm_factor_tco2e_per_ton",
            source="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
            span="derived_claims.l_materials.factor",
            text="15.5 tCO2e/ton",
        ),
    )


def _checked_claims(
    *,
    mn_share: Decimal = MN_SHARE,
) -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "actor_id",
            ACTOR_ID,
            "source:l-materials-composition",
            "platform_fixture",
        ),
        CheckedClaim(
            "material_family",
            MATERIAL_FAMILY,
            "source:l-materials-composition",
            "composition_submission",
        ),
        CheckedClaim(
            "ni_share",
            _number(NI_SHARE),
            "source:l-materials-composition",
            "composition_submission",
        ),
        CheckedClaim(
            "co_share",
            _number(CO_SHARE),
            "source:l-materials-composition",
            "composition_submission",
        ),
        CheckedClaim(
            "mn_share",
            _number(mn_share),
            "source:l-materials-composition",
            "composition_submission",
        ),
        CheckedClaim(
            "production_ton",
            PRODUCTION_TON,
            "source:l-materials-production",
            "composition_submission",
        ),
        CheckedClaim(
            "mapped_ncm_factor_tco2e_per_ton",
            _number(MAPPED_NCM_FACTOR_TCO2E_PER_TON),
            "source:l-materials-ncm-factor",
            "composition_factor_fixture",
        ),
    )


def _resolved_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="composition_total_validated",
            field="ncm_composition",
            reason="shares_sum_to_one",
            obligation_id=COMPOSITION_TOTAL_OBLIGATION_ID,
        ),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=COMPOSITION_FACTOR_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.ncm811_composition",
            reference_type="composition_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:l-materials-ncm-factor",),
        ),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    composition_total = NI_SHARE + CO_SHARE + MN_SHARE
    emission = Decimal(PRODUCTION_TON) * MAPPED_NCM_FACTOR_TCO2E_PER_TON
    composition_step = CalculationStep(
        step_id="composition-total",
        operation="sum",
        input_ids=("ni_share", "co_share", "mn_share"),
        output_value=_number(composition_total),
    )
    emission_step = CalculationStep(
        step_id="ncm-emission-tco2e",
        operation="multiply",
        input_ids=("production_ton", COMPOSITION_FACTOR_BINDING_ID),
        output_value=_number(emission),
        output_unit="tCO2e",
    )
    return (
        DerivedClaim(
            claim_id=COMPOSITION_TOTAL_CLAIM_ID,
            field="composition_total",
            value=_number(composition_total),
            unit=None,
            origin="composition_rule_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{COMPOSITION_TOTAL_CLAIM_ID}",
                formula_id=FORMULA_ID,
                steps=(composition_step,),
            ),
        ),
        DerivedClaim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="l_materials_final_emission_tco2e",
            value=_number(emission),
            unit="tCO2e",
            origin="composition_factor_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{FINAL_EMISSION_CLAIM_ID}",
                formula_id=FORMULA_ID,
                input_claim_ids=(COMPOSITION_TOTAL_CLAIM_ID,),
                reference_binding_ids=(COMPOSITION_FACTOR_BINDING_ID,),
                steps=(composition_step, emission_step),
            ),
        ),
    )


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


L_MATERIALS_COMPOSITION_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="L-Materials NCM composition roll-up",
    run=run_l_materials_composition_rollup_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=("composition_total_validated",),
        required_reference_binding_ids=(COMPOSITION_FACTOR_BINDING_ID,),
        required_derived_claim_ids=(
            COMPOSITION_TOTAL_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(COMPOSITION_FACTOR_BINDING_ID,),
        required_receipt_derived_claim_ids=(
            COMPOSITION_TOTAL_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{COMPOSITION_TOTAL_CLAIM_ID}",
            f"trace:{FINAL_EMISSION_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "COMPOSITION_FACTOR_BINDING_ID",
    "COMPOSITION_TOTAL_OBLIGATION_ID",
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "L_MATERIALS_COMPOSITION_SCENARIO",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "SCENARIO_ID",
    "invalid_l_materials_composition_report",
    "l_materials_composition_rollup_report",
    "run_l_materials_composition_rollup_scenario",
]
