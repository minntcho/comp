from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from comp import PublicOutputSpec, SubjectRef, build_public_output
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    ValidationReport,
    CalculatedClaim,
    EvidenceRef,
    CanonicalReference,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "l_energy.alpha_physical_allocation_correction.v1"
PROJECTION_ID = "l-energy-alpha-physical-allocation-correction"
PROJECTION_FIELDS = (
    "actor_id",
    "allocation_method",
    "allocation_weight",
    "alpha_metal_final_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "alpha_metal",
    "allocation_method": "physical_allocation",
    "allocation_weight": 0.44,
    "alpha_metal_final_emission_tco2e": 5306,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:alpha-metal-physical-allocation"
PUBLIC_ROW_ID = "public-row:alpha-metal-physical-allocation-correction"

FORMULA_ID = "pcf.alpha_metal_physical_allocation.v1"
ELECTRICITY_BINDING_ID = "bind:alpha-metal:electricity_factor"
LNG_BINDING_ID = "bind:alpha-metal:lng_factor"
FINAL_EMISSION_CLAIM_ID = "alpha-metal:final_emission_tco2e"

ACTOR_ID = "alpha_metal"
ALLOCATION_METHOD = "physical_allocation"
TARGET_PANEL_TON = 4400
TARGET_RESIDENCE_HOURS = 10
COMPARISON_PANEL_TON = 11200
COMPARISON_RESIDENCE_HOURS = 5
TOTAL_ELECTRICITY_MWH = 20000
TOTAL_LNG_NM3 = 500000
ELECTRICITY_FACTOR_TCO2E_PER_MWH = Decimal("0.478")
LNG_FACTOR_TCO2E_PER_NM3 = Decimal("0.0022")

RESOLVER_STEPS = (
    "load_platform_alpha_correction_fixture",
    "retain_invalid_original_as_audit_context",
    "deterministic_physical_allocation_formula",
    "bind_electricity_and_lng_factors",
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


def run_alpha_physical_allocation_correction_scenario():
    report = alpha_physical_allocation_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
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
    )


def alpha_physical_allocation_report() -> ValidationReport:
    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=_evidence_refs(),
            checked_claims=_checked_claims(),
            canonical_references=_canonical_references(),
            calculated_claims=_calculated_claims(),
            can_build_public_output=True,
        )
    )


def _evidence_refs() -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            witness_id="source:alpha-metal-original-invalid-allocation",
            field="allocation_method",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.alpha_metal.raw_submission.allocation_method",
            text="revenue_share allocation_share=0.30",
        ),
        EvidenceRef(
            witness_id="source:alpha-metal-physical-correction",
            field="allocation_method",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.alpha_metal.corrected_submission",
            text="physical_allocation rolling_residence_time provided",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    witness_id = "source:alpha-metal-physical-correction"
    return (
        CheckedClaim("actor_id", ACTOR_ID, witness_id, "supplier_correction"),
        CheckedClaim(
            "allocation_method",
            ALLOCATION_METHOD,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim(
            "target_panel_ton",
            TARGET_PANEL_TON,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim(
            "target_residence_hours",
            TARGET_RESIDENCE_HOURS,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim(
            "comparison_panel_ton",
            COMPARISON_PANEL_TON,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim(
            "comparison_residence_hours",
            COMPARISON_RESIDENCE_HOURS,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim(
            "total_electricity_mwh",
            TOTAL_ELECTRICITY_MWH,
            witness_id,
            "supplier_correction",
        ),
        CheckedClaim("total_lng_nm3", TOTAL_LNG_NM3, witness_id, "supplier_correction"),
    )


def _canonical_references() -> tuple[CanonicalReference, ...]:
    return (
        CanonicalReference(
            binding_id=ELECTRICITY_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.electricity_mwh",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
        CanonicalReference(
            binding_id=LNG_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.lng_nm3",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
    )


def _calculated_claims() -> tuple[CalculatedClaim, ...]:
    values = _calculated_values()
    return (
        _derived_claim(
            claim_id="alpha-metal:allocation_weight",
            field="allocation_weight",
            value=values["allocation_weight"],
            unit=None,
            steps=(
                values["target_weight_step"],
                values["comparison_weight_step"],
                values["allocation_weight_step"],
            ),
        ),
        _derived_claim(
            claim_id="alpha-metal:allocated_electricity_mwh",
            field="allocated_electricity_mwh",
            value=values["allocated_electricity_mwh"],
            unit="MWh",
            input_claim_ids=("alpha-metal:allocation_weight",),
            steps=(values["allocated_electricity_step"],),
        ),
        _derived_claim(
            claim_id="alpha-metal:electricity_emission_tco2e",
            field="electricity_emission_tco2e",
            value=values["electricity_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=("alpha-metal:allocated_electricity_mwh",),
            reference_binding_ids=(ELECTRICITY_BINDING_ID,),
            steps=(values["electricity_emission_step"],),
        ),
        _derived_claim(
            claim_id="alpha-metal:lng_emission_tco2e",
            field="lng_emission_tco2e",
            value=values["lng_emission_tco2e"],
            unit="tCO2e",
            reference_binding_ids=(LNG_BINDING_ID,),
            steps=(values["lng_emission_step"],),
        ),
        _derived_claim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="alpha_metal_final_emission_tco2e",
            value=values["final_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(
                "alpha-metal:electricity_emission_tco2e",
                "alpha-metal:lng_emission_tco2e",
            ),
            reference_binding_ids=(ELECTRICITY_BINDING_ID, LNG_BINDING_ID),
            steps=(
                values["target_weight_step"],
                values["comparison_weight_step"],
                values["allocation_weight_step"],
                values["allocated_electricity_step"],
                values["electricity_emission_step"],
                values["lng_emission_step"],
                values["final_emission_step"],
            ),
        ),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value,
    unit: str | None,
    input_claim_ids: tuple[str, ...] = (),
    reference_binding_ids: tuple[str, ...] = (),
    steps: tuple[CalculationStep, ...],
) -> CalculatedClaim:
    return CalculatedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin="supplier_correction_calculated",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _calculated_values() -> dict[str, object]:
    target_weight = TARGET_PANEL_TON * TARGET_RESIDENCE_HOURS
    comparison_weight = COMPARISON_PANEL_TON * COMPARISON_RESIDENCE_HOURS
    allocation_weight = _as_decimal(target_weight) / (
        _as_decimal(target_weight) + _as_decimal(comparison_weight)
    )
    allocated_electricity = _as_decimal(TOTAL_ELECTRICITY_MWH) * allocation_weight
    electricity_emission = allocated_electricity * ELECTRICITY_FACTOR_TCO2E_PER_MWH
    lng_emission = _as_decimal(TOTAL_LNG_NM3) * LNG_FACTOR_TCO2E_PER_NM3
    final_emission = _round_half_up(electricity_emission + lng_emission)

    return {
        "allocation_weight": _number(allocation_weight),
        "allocated_electricity_mwh": _number(allocated_electricity),
        "electricity_emission_tco2e": _number(electricity_emission),
        "lng_emission_tco2e": _number(lng_emission),
        "final_emission_tco2e": final_emission,
        "target_weight_step": CalculationStep(
            step_id="target-weight-ton-hours",
            operation="multiply",
            input_ids=("target_panel_ton", "target_residence_hours"),
            output_value=target_weight,
            output_unit="ton*h",
        ),
        "comparison_weight_step": CalculationStep(
            step_id="comparison-weight-ton-hours",
            operation="multiply",
            input_ids=("comparison_panel_ton", "comparison_residence_hours"),
            output_value=comparison_weight,
            output_unit="ton*h",
        ),
        "allocation_weight_step": CalculationStep(
            step_id="allocation-weight",
            operation="divide",
            input_ids=("target-weight-ton-hours", "comparison-weight-ton-hours"),
            output_value=_number(allocation_weight),
        ),
        "allocated_electricity_step": CalculationStep(
            step_id="allocated-electricity-mwh",
            operation="multiply",
            input_ids=("total_electricity_mwh", "allocation-weight"),
            output_value=_number(allocated_electricity),
            output_unit="MWh",
        ),
        "electricity_emission_step": CalculationStep(
            step_id="electricity-emission-tco2e",
            operation="multiply",
            input_ids=("allocated-electricity-mwh", ELECTRICITY_BINDING_ID),
            output_value=_number(electricity_emission),
            output_unit="tCO2e",
        ),
        "lng_emission_step": CalculationStep(
            step_id="lng-emission-tco2e",
            operation="multiply",
            input_ids=("total_lng_nm3", LNG_BINDING_ID),
            output_value=_number(lng_emission),
            output_unit="tCO2e",
        ),
        "final_emission_step": CalculationStep(
            step_id="rounded-final-emission-tco2e",
            operation="round",
            input_ids=("electricity-emission-tco2e", "lng-emission-tco2e"),
            output_value=final_emission,
            output_unit="tCO2e",
        ),
    }


def _projection_source(report: ValidationReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values


def _round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _as_decimal(value: int | float | Decimal) -> Decimal:
    return Decimal(str(value))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


ALPHA_PHYSICAL_ALLOCATION_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Alpha Metal physical allocation correction",
    run=run_alpha_physical_allocation_correction_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_reference_binding_ids=(ELECTRICITY_BINDING_ID, LNG_BINDING_ID),
        required_derived_claim_ids=(
            "alpha-metal:allocation_weight",
            "alpha-metal:allocated_electricity_mwh",
            "alpha-metal:electricity_emission_tco2e",
            "alpha-metal:lng_emission_tco2e",
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(
            ELECTRICITY_BINDING_ID,
            LNG_BINDING_ID,
        ),
        required_receipt_derived_claim_ids=(
            "alpha-metal:allocation_weight",
            "alpha-metal:allocated_electricity_mwh",
            "alpha-metal:electricity_emission_tco2e",
            "alpha-metal:lng_emission_tco2e",
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            "trace:alpha-metal:allocation_weight",
            "trace:alpha-metal:allocated_electricity_mwh",
            "trace:alpha-metal:electricity_emission_tco2e",
            "trace:alpha-metal:lng_emission_tco2e",
            "trace:alpha-metal:final_emission_tco2e",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "ALPHA_PHYSICAL_ALLOCATION_SCENARIO",
    "ELECTRICITY_BINDING_ID",
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "LNG_BINDING_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "SCENARIO_ID",
    "alpha_physical_allocation_report",
    "run_alpha_physical_allocation_correction_scenario",
]
