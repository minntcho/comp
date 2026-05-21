from __future__ import annotations

from decimal import Decimal, ROUND_DOWN

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


SCENARIO_ID = "l_energy.final_bottom_up_pcf_rollup.v1"
PROJECTION_ID = "l-energy-final-bottom-up-pcf-rollup"
PROJECTION_FIELDS = (
    "actor_id",
    "product_id",
    "l_energy_total_emission_tco2e",
    "pack_count",
    "total_energy_gwh",
    "kg_co2e_per_pack",
    "kg_co2e_per_kwh",
)
EXPECTED_PROJECTION = {
    "actor_id": "l_energy",
    "product_id": "battery_pack",
    "l_energy_total_emission_tco2e": 199994,
    "pack_count": 100000,
    "total_energy_gwh": 7.5,
    "kg_co2e_per_pack": 1999.94,
    "kg_co2e_per_kwh": 26.66,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:final-bottom-up-rollup"
PUBLIC_ROW_ID = "public-row:final-bottom-up-pcf-rollup"

FORMULA_ID = "pcf.l_energy_final_bottom_up_rollup.v1"
TIER0_CHILD_BINDING_ID = "bind:final-rollup:tier0_l_energy_child_receipt"
C_PACK_CHILD_BINDING_ID = "bind:final-rollup:c_pack_child_receipt"
CARBON_TECH_CHILD_BINDING_ID = "bind:final-rollup:carbon_tech_child_receipt"
L_MATERIALS_CHILD_BINDING_ID = "bind:final-rollup:l_materials_child_receipt"
TOTAL_EMISSION_CLAIM_ID = "l-energy:final_total_emission_tco2e"
PACK_INTENSITY_CLAIM_ID = "l-energy:kg_co2e_per_pack"
KWH_INTENSITY_CLAIM_ID = "l-energy:kg_co2e_per_kwh"
CHILD_AUTHORIZATION_OBLIGATION_ID = (
    "final-rollup:children:accepted_or_proxy_authorized"
)
ROLLUP_SNAPSHOT_OBLIGATION_ID = "final-rollup:snapshot:created"

TIER0_CHILD_CLAIM_ID = "l-energy:own_emission_tco2e"
C_PACK_CHILD_CLAIM_ID = "c-pack:final_emission_tco2e"
CARBON_TECH_CHILD_CLAIM_ID = "carbon-tech:final_emission_tco2e"
L_MATERIALS_CHILD_CLAIM_ID = "l-materials:final_emission_tco2e"

ACTOR_ID = "l_energy"
PRODUCT_ID = "battery_pack"
PACK_COUNT = 100000
TOTAL_ENERGY_GWH = Decimal("7.5")
L_ENERGY_OWN_EMISSION_TCO2E = 1695
C_PACK_FINAL_EMISSION_TCO2E = 10534
CARBON_TECH_FINAL_EMISSION_TCO2E = 13390
L_MATERIALS_FINAL_EMISSION_TCO2E = 174375

RESOLVER_STEPS = (
    "load_platform_final_l_energy_fixture",
    "require_accepted_or_proxy_authorized_child_claims",
    "bind_child_receipts",
    "create_rollup_snapshot",
    "calculate_bottom_up_total",
    "calculate_pack_and_kwh_intensity",
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


def run_final_bottom_up_rollup_scenario():
    report = final_bottom_up_rollup_report()
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


def final_bottom_up_rollup_report() -> CompileReport:
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
            witness_id="source:final-rollup-production",
            field="production_volume",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.l_energy.final_product",
            text="100,000 packs; 7.5 GWh",
        ),
        EvidenceWitness(
            witness_id="source:final-rollup-child-receipts",
            field="child_receipts",
            source="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
            span="derived_claims.final_rollup.children",
            text=(
                "L-Energy own 1,695; C-Pack 10,534; Carbon Tech 13,390; "
                "L-Materials 174,375"
            ),
        ),
        EvidenceWitness(
            witness_id="source:final-rollup-snapshot",
            field="rollup_snapshot",
            source="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
            span="final_rollup.snapshot",
            text="bottom-up total 199,994 tCO2e",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "actor_id",
            ACTOR_ID,
            "source:final-rollup-production",
            "platform_fixture",
        ),
        CheckedClaim(
            "product_id",
            PRODUCT_ID,
            "source:final-rollup-production",
            "platform_fixture",
        ),
        CheckedClaim(
            "pack_count",
            PACK_COUNT,
            "source:final-rollup-production",
            "platform_fixture",
        ),
        CheckedClaim(
            "total_energy_gwh",
            _number(TOTAL_ENERGY_GWH),
            "source:final-rollup-production",
            "platform_fixture",
        ),
        CheckedClaim(
            "l_energy_own_emission_tco2e",
            L_ENERGY_OWN_EMISSION_TCO2E,
            "source:final-rollup-child-receipts",
            "child_receipt",
        ),
        CheckedClaim(
            "c_pack_final_emission_tco2e",
            C_PACK_FINAL_EMISSION_TCO2E,
            "source:final-rollup-child-receipts",
            "child_receipt",
        ),
        CheckedClaim(
            "carbon_tech_final_emission_tco2e",
            CARBON_TECH_FINAL_EMISSION_TCO2E,
            "source:final-rollup-child-receipts",
            "child_receipt",
        ),
        CheckedClaim(
            "l_materials_final_emission_tco2e",
            L_MATERIALS_FINAL_EMISSION_TCO2E,
            "source:final-rollup-child-receipts",
            "child_receipt",
        ),
        CheckedClaim(
            "c_pack_dependency_kind",
            "proxy_authorized_child_rollup",
            "source:final-rollup-child-receipts",
            "child_receipt",
        ),
    )


def _resolved_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="child_claims_accepted_or_proxy_authorized",
            field="final_rollup_children",
            reason="tier0_c_pack_carbon_tech_l_materials_paths_available",
            obligation_id=CHILD_AUTHORIZATION_OBLIGATION_ID,
        ),
        ProofObligation(
            kind="rollup_snapshot_created",
            field="final_bottom_up_rollup",
            reason="child_claim_values_frozen_for_final_projection",
            obligation_id=ROLLUP_SNAPSHOT_OBLIGATION_ID,
        ),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        _child_receipt_binding(
            binding_id=TIER0_CHILD_BINDING_ID,
            reference_id="scenario:l_energy.tier0_physical_allocation.v1",
        ),
        _child_receipt_binding(
            binding_id=C_PACK_CHILD_BINDING_ID,
            reference_id="scenario:l_energy.c_pack_yield_rollup.v1",
        ),
        _child_receipt_binding(
            binding_id=CARBON_TECH_CHILD_BINDING_ID,
            reference_id="scenario:l_energy.carbon_tech_certificate_submission.v1",
        ),
        _child_receipt_binding(
            binding_id=L_MATERIALS_CHILD_BINDING_ID,
            reference_id="scenario:l_energy.l_materials_composition_rollup.v1",
        ),
    )


def _child_receipt_binding(*, binding_id: str, reference_id: str) -> ReferenceBinding:
    return ReferenceBinding(
        binding_id=binding_id,
        claim_id=SCENARIO_ID,
        reference_id=reference_id,
        reference_type="child_receipt",
        selector_rule_id="platform.expected_receipt.fixture",
        source_witness_ids=("source:final-rollup-child-receipts",),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    values = _calculated_values()
    return (
        _derived_claim(
            claim_id=TOTAL_EMISSION_CLAIM_ID,
            field="l_energy_total_emission_tco2e",
            value=values["total_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(
                TIER0_CHILD_CLAIM_ID,
                C_PACK_CHILD_CLAIM_ID,
                CARBON_TECH_CHILD_CLAIM_ID,
                L_MATERIALS_CHILD_CLAIM_ID,
            ),
            steps=(values["bottom_up_total_step"],),
        ),
        _derived_claim(
            claim_id=PACK_INTENSITY_CLAIM_ID,
            field="kg_co2e_per_pack",
            value=values["kg_co2e_per_pack"],
            unit="kgCO2e/pack",
            input_claim_ids=(TOTAL_EMISSION_CLAIM_ID, "pack_count"),
            steps=(
                values["total_emission_kg_step"],
                values["pack_intensity_step"],
            ),
        ),
        _derived_claim(
            claim_id=KWH_INTENSITY_CLAIM_ID,
            field="kg_co2e_per_kwh",
            value=values["kg_co2e_per_kwh"],
            unit="kgCO2e/kWh",
            input_claim_ids=(TOTAL_EMISSION_CLAIM_ID, "total_energy_gwh"),
            steps=(
                values["total_emission_kg_step"],
                values["total_energy_kwh_step"],
                values["kwh_intensity_raw_step"],
                values["kwh_intensity_step"],
            ),
        ),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value,
    unit: str,
    input_claim_ids: tuple[str, ...],
    steps: tuple[CalculationStep, ...],
) -> DerivedClaim:
    child_binding_ids = (
        TIER0_CHILD_BINDING_ID,
        C_PACK_CHILD_BINDING_ID,
        CARBON_TECH_CHILD_BINDING_ID,
        L_MATERIALS_CHILD_BINDING_ID,
    )
    return DerivedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin="final_bottom_up_rollup_calculated",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=child_binding_ids,
            steps=steps,
        ),
    )


def _calculated_values() -> dict[str, object]:
    total_emission = (
        Decimal(L_ENERGY_OWN_EMISSION_TCO2E)
        + Decimal(C_PACK_FINAL_EMISSION_TCO2E)
        + Decimal(CARBON_TECH_FINAL_EMISSION_TCO2E)
        + Decimal(L_MATERIALS_FINAL_EMISSION_TCO2E)
    )
    total_emission_kg = total_emission * Decimal("1000")
    total_energy_kwh = TOTAL_ENERGY_GWH * Decimal("1000000")
    kg_per_pack = _round_2(total_emission_kg / Decimal(PACK_COUNT))
    kg_per_kwh_raw = total_emission_kg / total_energy_kwh
    kg_per_kwh = _truncate_2(kg_per_kwh_raw)

    return {
        "total_emission_tco2e": _number(total_emission),
        "total_emission_kgco2e": _number(total_emission_kg),
        "total_energy_kwh": _number(total_energy_kwh),
        "kg_co2e_per_pack": kg_per_pack,
        "kg_co2e_per_kwh_raw": float(kg_per_kwh_raw),
        "kg_co2e_per_kwh": kg_per_kwh,
        "bottom_up_total_step": CalculationStep(
            step_id="bottom-up-total-tco2e",
            operation="sum",
            input_ids=(
                TIER0_CHILD_CLAIM_ID,
                C_PACK_CHILD_CLAIM_ID,
                CARBON_TECH_CHILD_CLAIM_ID,
                L_MATERIALS_CHILD_CLAIM_ID,
            ),
            output_value=_number(total_emission),
            output_unit="tCO2e",
        ),
        "total_emission_kg_step": CalculationStep(
            step_id="total-emission-kgco2e",
            operation="multiply",
            input_ids=(TOTAL_EMISSION_CLAIM_ID, "kg_per_tco2e"),
            output_value=_number(total_emission_kg),
            output_unit="kgCO2e",
        ),
        "pack_intensity_step": CalculationStep(
            step_id="kg-co2e-per-pack",
            operation="divide",
            input_ids=("total-emission-kgco2e", "pack_count"),
            output_value=kg_per_pack,
            output_unit="kgCO2e/pack",
        ),
        "total_energy_kwh_step": CalculationStep(
            step_id="total-energy-kwh",
            operation="multiply",
            input_ids=("total_energy_gwh", "kwh_per_gwh"),
            output_value=_number(total_energy_kwh),
            output_unit="kWh",
        ),
        "kwh_intensity_raw_step": CalculationStep(
            step_id="kg-co2e-per-kwh-raw",
            operation="divide",
            input_ids=("total-emission-kgco2e", "total-energy-kwh"),
            output_value=float(kg_per_kwh_raw),
            output_unit="kgCO2e/kWh",
        ),
        "kwh_intensity_step": CalculationStep(
            step_id="kg-co2e-per-kwh",
            operation="truncate_2dp",
            input_ids=("kg-co2e-per-kwh-raw",),
            output_value=kg_per_kwh,
            output_unit="kgCO2e/kWh",
        ),
    }


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _round_2(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01")))


def _truncate_2(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_DOWN))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


FINAL_BOTTOM_UP_ROLLUP_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Final L-Energy bottom-up PCF roll-up",
    run=run_final_bottom_up_rollup_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=(
            "child_claims_accepted_or_proxy_authorized",
            "rollup_snapshot_created",
        ),
        required_reference_binding_ids=(
            TIER0_CHILD_BINDING_ID,
            C_PACK_CHILD_BINDING_ID,
            CARBON_TECH_CHILD_BINDING_ID,
            L_MATERIALS_CHILD_BINDING_ID,
        ),
        required_derived_claim_ids=(
            TOTAL_EMISSION_CLAIM_ID,
            PACK_INTENSITY_CLAIM_ID,
            KWH_INTENSITY_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(
            TIER0_CHILD_BINDING_ID,
            C_PACK_CHILD_BINDING_ID,
            CARBON_TECH_CHILD_BINDING_ID,
            L_MATERIALS_CHILD_BINDING_ID,
        ),
        required_receipt_derived_claim_ids=(
            TOTAL_EMISSION_CLAIM_ID,
            PACK_INTENSITY_CLAIM_ID,
            KWH_INTENSITY_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{TOTAL_EMISSION_CLAIM_ID}",
            f"trace:{PACK_INTENSITY_CLAIM_ID}",
            f"trace:{KWH_INTENSITY_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "CARBON_TECH_CHILD_BINDING_ID",
    "C_PACK_CHILD_BINDING_ID",
    "EXPECTED_PROJECTION",
    "FINAL_BOTTOM_UP_ROLLUP_SCENARIO",
    "KWH_INTENSITY_CLAIM_ID",
    "L_MATERIALS_CHILD_BINDING_ID",
    "PACK_INTENSITY_CLAIM_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "SCENARIO_ID",
    "TIER0_CHILD_BINDING_ID",
    "TOTAL_EMISSION_CLAIM_ID",
    "final_bottom_up_rollup_report",
    "run_final_bottom_up_rollup_scenario",
]
