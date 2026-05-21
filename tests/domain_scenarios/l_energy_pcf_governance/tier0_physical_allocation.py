from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
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


SCENARIO_ID = "l_energy.tier0_physical_allocation.v1"
PROJECTION_ID = "l-energy-tier0-physical-allocation"
PROJECTION_FIELDS = (
    "actor_id",
    "site_id",
    "allocation_method",
    "target_allocation_share",
    "l_energy_own_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "l_energy",
    "site_id": "ocheong_plant_1",
    "allocation_method": "physical_allocation",
    "target_allocation_share": 0.5,
    "l_energy_own_emission_tco2e": 1695,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:tier0-physical-allocation"
PUBLIC_ROW_ID = "public-row:tier0-physical-allocation"

FORMULA_ID = "pcf.l_energy_tier0_physical_allocation.v1"
ELECTRICITY_BINDING_ID = "bind:l-energy-tier0:electricity_factor"
LNG_BINDING_ID = "bind:l-energy-tier0:lng_factor"
SHARE_CLAIM_ID = "l-energy-tier0:target_allocation_share"
ALLOCATED_ELECTRICITY_CLAIM_ID = "l-energy-tier0:allocated_electricity_mwh"
ALLOCATED_LNG_CLAIM_ID = "l-energy-tier0:allocated_lng_nm3"
ELECTRICITY_EMISSION_CLAIM_ID = "l-energy-tier0:electricity_emission_tco2e"
LNG_EMISSION_CLAIM_ID = "l-energy-tier0:lng_emission_tco2e"
FINAL_EMISSION_CLAIM_ID = "l-energy:own_emission_tco2e"

ACTOR_ID = "l_energy"
SITE_ID = "ocheong_plant_1"
ALLOCATION_METHOD = "physical_allocation"
DQR = "High"
LINE_A_MASS_TON = 50000
LINE_B_MASS_TON = 20000
LINE_C_MASS_TON = 30000
TOTAL_ELECTRICITY_MWH = 6400
TOTAL_LNG_NM3 = 150000
ELECTRICITY_FACTOR_TCO2E_PER_MWH = Decimal("0.478")
LNG_FACTOR_TCO2E_PER_NM3 = Decimal("0.0022")

RESOLVER_STEPS = (
    "load_platform_tier0_l_energy_fixture",
    "derive_line_mass_allocation_share",
    "allocate_site_energy",
    "bind_electricity_and_lng_factors",
    "calculate_l_energy_own_emission",
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


def run_tier0_physical_allocation_scenario():
    report = tier0_physical_allocation_report()
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


def tier0_physical_allocation_report() -> CompileReport:
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=_evidence_witnesses(),
            checked_claims=_checked_claims(),
            reference_bindings=_reference_bindings(),
            derived_claims=_derived_claims(),
            can_project_public_row=True,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id="source:l-energy-site-energy",
            field="site_energy",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.l_energy.site_energy",
            text="6,400 MWh electricity; 150,000 Nm3 LNG",
        ),
        EvidenceWitness(
            witness_id="source:l-energy-line-masses",
            field="line_masses",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.l_energy.line_masses",
            text="Line A/B/C 50,000/20,000/30,000 ton",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim("actor_id", ACTOR_ID, "source:l-energy-line-masses", "site_fixture"),
        CheckedClaim("site_id", SITE_ID, "source:l-energy-line-masses", "site_fixture"),
        CheckedClaim(
            "allocation_method",
            ALLOCATION_METHOD,
            "source:l-energy-line-masses",
            "site_fixture",
        ),
        CheckedClaim(
            "line_a_mass_ton",
            LINE_A_MASS_TON,
            "source:l-energy-line-masses",
            "site_fixture",
        ),
        CheckedClaim(
            "line_b_mass_ton",
            LINE_B_MASS_TON,
            "source:l-energy-line-masses",
            "site_fixture",
        ),
        CheckedClaim(
            "line_c_mass_ton",
            LINE_C_MASS_TON,
            "source:l-energy-line-masses",
            "site_fixture",
        ),
        CheckedClaim(
            "total_electricity_mwh",
            TOTAL_ELECTRICITY_MWH,
            "source:l-energy-site-energy",
            "site_fixture",
        ),
        CheckedClaim(
            "total_lng_nm3",
            TOTAL_LNG_NM3,
            "source:l-energy-site-energy",
            "site_fixture",
        ),
        CheckedClaim("dqr", DQR, "source:l-energy-line-masses", "site_fixture"),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=ELECTRICITY_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.electricity_mwh",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:l-energy-site-energy",),
        ),
        ReferenceBinding(
            binding_id=LNG_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.lng_nm3",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:l-energy-site-energy",),
        ),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    values = _calculated_values()
    return (
        _derived_claim(
            claim_id=SHARE_CLAIM_ID,
            field="target_allocation_share",
            value=values["target_allocation_share"],
            unit=None,
            steps=(values["total_mass_step"], values["allocation_share_step"]),
        ),
        _derived_claim(
            claim_id=ALLOCATED_ELECTRICITY_CLAIM_ID,
            field="allocated_electricity_mwh",
            value=values["allocated_electricity_mwh"],
            unit="MWh",
            input_claim_ids=(SHARE_CLAIM_ID,),
            steps=(values["allocated_electricity_step"],),
        ),
        _derived_claim(
            claim_id=ALLOCATED_LNG_CLAIM_ID,
            field="allocated_lng_nm3",
            value=values["allocated_lng_nm3"],
            unit="Nm3",
            input_claim_ids=(SHARE_CLAIM_ID,),
            steps=(values["allocated_lng_step"],),
        ),
        _derived_claim(
            claim_id=ELECTRICITY_EMISSION_CLAIM_ID,
            field="electricity_emission_tco2e",
            value=values["electricity_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(ALLOCATED_ELECTRICITY_CLAIM_ID,),
            reference_binding_ids=(ELECTRICITY_BINDING_ID,),
            steps=(values["electricity_emission_step"],),
        ),
        _derived_claim(
            claim_id=LNG_EMISSION_CLAIM_ID,
            field="lng_emission_tco2e",
            value=values["lng_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(ALLOCATED_LNG_CLAIM_ID,),
            reference_binding_ids=(LNG_BINDING_ID,),
            steps=(values["lng_emission_step"],),
        ),
        _derived_claim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="l_energy_own_emission_tco2e",
            value=values["own_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(ELECTRICITY_EMISSION_CLAIM_ID, LNG_EMISSION_CLAIM_ID),
            reference_binding_ids=(ELECTRICITY_BINDING_ID, LNG_BINDING_ID),
            steps=(
                values["total_mass_step"],
                values["allocation_share_step"],
                values["allocated_electricity_step"],
                values["allocated_lng_step"],
                values["electricity_emission_step"],
                values["lng_emission_step"],
                values["own_emission_step"],
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
) -> DerivedClaim:
    return DerivedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin="tier0_physical_allocation_calculated",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _calculated_values() -> dict[str, object]:
    total_mass = LINE_A_MASS_TON + LINE_B_MASS_TON + LINE_C_MASS_TON
    allocation_share = Decimal(LINE_A_MASS_TON) / Decimal(total_mass)
    allocated_electricity = Decimal(TOTAL_ELECTRICITY_MWH) * allocation_share
    allocated_lng = Decimal(TOTAL_LNG_NM3) * allocation_share
    electricity_emission = allocated_electricity * ELECTRICITY_FACTOR_TCO2E_PER_MWH
    lng_emission = allocated_lng * LNG_FACTOR_TCO2E_PER_NM3
    own_emission = _round_half_up(electricity_emission + lng_emission)

    return {
        "target_allocation_share": _number(allocation_share),
        "allocated_electricity_mwh": _number(allocated_electricity),
        "allocated_lng_nm3": _number(allocated_lng),
        "electricity_emission_tco2e": _number(electricity_emission),
        "lng_emission_tco2e": _number(lng_emission),
        "own_emission_tco2e": own_emission,
        "total_mass_step": CalculationStep(
            step_id="total-line-mass-ton",
            operation="sum",
            input_ids=("line_a_mass_ton", "line_b_mass_ton", "line_c_mass_ton"),
            output_value=total_mass,
            output_unit="ton",
        ),
        "allocation_share_step": CalculationStep(
            step_id="target-allocation-share",
            operation="divide",
            input_ids=("line_a_mass_ton", "total-line-mass-ton"),
            output_value=_number(allocation_share),
        ),
        "allocated_electricity_step": CalculationStep(
            step_id="allocated-electricity-mwh",
            operation="multiply",
            input_ids=("total_electricity_mwh", "target-allocation-share"),
            output_value=_number(allocated_electricity),
            output_unit="MWh",
        ),
        "allocated_lng_step": CalculationStep(
            step_id="allocated-lng-nm3",
            operation="multiply",
            input_ids=("total_lng_nm3", "target-allocation-share"),
            output_value=_number(allocated_lng),
            output_unit="Nm3",
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
            input_ids=("allocated-lng-nm3", LNG_BINDING_ID),
            output_value=_number(lng_emission),
            output_unit="tCO2e",
        ),
        "own_emission_step": CalculationStep(
            step_id="rounded-own-emission-tco2e",
            operation="round",
            input_ids=("electricity-emission-tco2e", "lng-emission-tco2e"),
            output_value=own_emission,
            output_unit="tCO2e",
        ),
    }


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


TIER0_PHYSICAL_ALLOCATION_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Tier 0 L-Energy physical allocation",
    run=run_tier0_physical_allocation_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_reference_binding_ids=(ELECTRICITY_BINDING_ID, LNG_BINDING_ID),
        required_derived_claim_ids=(
            SHARE_CLAIM_ID,
            ALLOCATED_ELECTRICITY_CLAIM_ID,
            ALLOCATED_LNG_CLAIM_ID,
            ELECTRICITY_EMISSION_CLAIM_ID,
            LNG_EMISSION_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(
            ELECTRICITY_BINDING_ID,
            LNG_BINDING_ID,
        ),
        required_receipt_derived_claim_ids=(
            SHARE_CLAIM_ID,
            ALLOCATED_ELECTRICITY_CLAIM_ID,
            ALLOCATED_LNG_CLAIM_ID,
            ELECTRICITY_EMISSION_CLAIM_ID,
            LNG_EMISSION_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{SHARE_CLAIM_ID}",
            f"trace:{ALLOCATED_ELECTRICITY_CLAIM_ID}",
            f"trace:{ALLOCATED_LNG_CLAIM_ID}",
            f"trace:{ELECTRICITY_EMISSION_CLAIM_ID}",
            f"trace:{LNG_EMISSION_CLAIM_ID}",
            f"trace:{FINAL_EMISSION_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "ELECTRICITY_BINDING_ID",
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "LNG_BINDING_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "SCENARIO_ID",
    "TIER0_PHYSICAL_ALLOCATION_SCENARIO",
    "run_tier0_physical_allocation_scenario",
    "tier0_physical_allocation_report",
]
