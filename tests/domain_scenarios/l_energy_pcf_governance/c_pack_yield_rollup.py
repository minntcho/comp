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
    ValidationRequirement,
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


SCENARIO_ID = "l_energy.c_pack_yield_rollup.v1"
PROJECTION_ID = "l-energy-c-pack-yield-rollup"
PROJECTION_FIELDS = (
    "actor_id",
    "required_lower_tier_input_ton",
    "lower_tier_rollup_tco2e",
    "verified_primary_coverage",
    "proxy_coverage",
    "c_pack_final_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "c_pack",
    "required_lower_tier_input_ton": 6300,
    "lower_tier_rollup_tco2e": 10056,
    "verified_primary_coverage": 0.698,
    "proxy_coverage": 0.302,
    "c_pack_final_emission_tco2e": 10534,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:c-pack-yield-rollup"
PUBLIC_ROW_ID = "public-row:c-pack-yield-rollup"

FORMULA_ID = "pcf.c_pack_yield_rollup.v1"
ELECTRICITY_BINDING_ID = "bind:c-pack:assembly_electricity_factor"
REQUIRED_INPUT_CLAIM_ID = "c-pack:required_lower_tier_input_ton"
OWN_EMISSION_CLAIM_ID = "c-pack:own_emission_tco2e"
LOWER_TIER_ROLLUP_CLAIM_ID = "c-pack:lower_tier_rollup_tco2e"
VERIFIED_PRIMARY_COVERAGE_CLAIM_ID = "c-pack:verified_primary_coverage"
PROXY_COVERAGE_CLAIM_ID = "c-pack:proxy_coverage"
FINAL_EMISSION_CLAIM_ID = "c-pack:final_emission_tco2e"
ALPHA_CHILD_CLAIM_ID = "alpha-metal:final_emission_tco2e"
STEEL_PROXY_CHILD_CLAIM_ID = "steel-frame:final_emission_tco2e"
CHILD_CLAIMS_OBLIGATION_ID = "c-pack:child_claims:accepted_alpha_and_proxy_steel"
PROXY_DEPENDENCY_OBLIGATION_ID = (
    "c-pack:steel_frame_dependency:steel_proxy_dependency_cited"
)

ACTOR_ID = "c_pack"
ASSEMBLY_ELECTRICITY_MWH = 1000
ELECTRICITY_FACTOR_TCO2E_PER_MWH = Decimal("0.478")
HOUSING_OUTPUT_TON = 6000
SCRAP_LOSS_RATE = Decimal("0.05")
ALPHA_METAL_INPUT_TON = 4400
MISSING_STEEL_INPUT_TON = 1900
ALPHA_METAL_EMISSION_TCO2E = 5306
STEEL_FRAME_PROXY_EMISSION_TCO2E = 4750

RESOLVER_STEPS = (
    "load_platform_c_pack_yield_fixture",
    "derive_required_lower_tier_input",
    "attach_alpha_and_steel_child_claims",
    "preserve_steel_proxy_dependency",
    "bind_assembly_electricity_factor",
    "calculate_child_rollup",
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


def run_c_pack_yield_rollup_scenario():
    report = c_pack_yield_rollup_report()
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


def c_pack_yield_rollup_report() -> ValidationReport:
    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=_evidence_refs(),
            checked_claims=_checked_claims(),
            resolved_validation_requirements=_resolved_validation_requirements(),
            canonical_references=_canonical_references(),
            calculated_claims=_calculated_claims(),
            can_build_public_output=True,
        )
    )


def _evidence_refs() -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            witness_id="source:c-pack-yield-fixture",
            field="housing_output_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.c_pack.housing_output_ton",
            text="housing output 6,000 ton; scrap loss 5%",
        ),
        EvidenceRef(
            witness_id="source:c-pack-assembly-electricity",
            field="assembly_electricity_mwh",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.c_pack.assembly_electricity_mwh",
            text="1,000 MWh",
        ),
        EvidenceRef(
            witness_id="source:c-pack-child-claims",
            field="lower_tier_child_claims",
            source="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
            span="calculated_claims.c_pack.children",
            text="Alpha Metal 5,306; Steel Frame proxy 4,750",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "actor_id",
            ACTOR_ID,
            "source:c-pack-yield-fixture",
            "platform_fixture",
        ),
        CheckedClaim(
            "assembly_electricity_mwh",
            ASSEMBLY_ELECTRICITY_MWH,
            "source:c-pack-assembly-electricity",
            "platform_fixture",
        ),
        CheckedClaim(
            "housing_output_ton",
            HOUSING_OUTPUT_TON,
            "source:c-pack-yield-fixture",
            "platform_fixture",
        ),
        CheckedClaim(
            "scrap_loss_rate",
            _number(SCRAP_LOSS_RATE),
            "source:c-pack-yield-fixture",
            "platform_fixture",
        ),
        CheckedClaim(
            "alpha_metal_input_ton",
            ALPHA_METAL_INPUT_TON,
            "source:c-pack-child-claims",
            "child_receipt",
        ),
        CheckedClaim(
            "missing_steel_input_ton",
            MISSING_STEEL_INPUT_TON,
            "source:c-pack-child-claims",
            "proxy_child_receipt",
        ),
        CheckedClaim(
            "alpha_metal_final_emission_tco2e",
            ALPHA_METAL_EMISSION_TCO2E,
            "source:c-pack-child-claims",
            "child_receipt",
        ),
        CheckedClaim(
            "steel_frame_final_emission_tco2e",
            STEEL_FRAME_PROXY_EMISSION_TCO2E,
            "source:c-pack-child-claims",
            "proxy_child_receipt",
        ),
        CheckedClaim(
            "steel_frame_dependency_kind",
            "proxy_assignment",
            "source:c-pack-child-claims",
            "proxy_child_receipt",
        ),
    )


def _resolved_validation_requirements() -> tuple[ValidationRequirement, ...]:
    return (
        ValidationRequirement(
            kind="child_claims_available",
            field="c_pack_lower_tier_children",
            reason="accepted_alpha_and_proxy_steel_claims",
            requirement_id=CHILD_CLAIMS_OBLIGATION_ID,
        ),
        ValidationRequirement(
            kind="proxy_dependency_preserved",
            field="steel_frame_final_emission_tco2e",
            reason="steel_proxy_dependency_cited",
            requirement_id=PROXY_DEPENDENCY_OBLIGATION_ID,
        ),
    )


def _canonical_references() -> tuple[CanonicalReference, ...]:
    return (
        CanonicalReference(
            binding_id=ELECTRICITY_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.electricity_mwh",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:c-pack-assembly-electricity",),
        ),
    )


def _calculated_claims() -> tuple[CalculatedClaim, ...]:
    values = _calculated_values()
    return (
        _derived_claim(
            claim_id=REQUIRED_INPUT_CLAIM_ID,
            field="required_lower_tier_input_ton",
            value=values["required_lower_tier_input_ton"],
            unit="ton",
            steps=(values["required_input_step"],),
        ),
        _derived_claim(
            claim_id=OWN_EMISSION_CLAIM_ID,
            field="c_pack_own_emission_tco2e",
            value=values["own_emission_tco2e"],
            unit="tCO2e",
            reference_binding_ids=(ELECTRICITY_BINDING_ID,),
            steps=(values["own_emission_step"],),
        ),
        _derived_claim(
            claim_id=LOWER_TIER_ROLLUP_CLAIM_ID,
            field="lower_tier_rollup_tco2e",
            value=values["lower_tier_rollup_tco2e"],
            unit="tCO2e",
            input_claim_ids=(ALPHA_CHILD_CLAIM_ID, STEEL_PROXY_CHILD_CLAIM_ID),
            steps=(values["lower_tier_rollup_step"],),
        ),
        _derived_claim(
            claim_id=VERIFIED_PRIMARY_COVERAGE_CLAIM_ID,
            field="verified_primary_coverage",
            value=values["verified_primary_coverage"],
            unit=None,
            input_claim_ids=(REQUIRED_INPUT_CLAIM_ID,),
            steps=(values["verified_coverage_step"],),
        ),
        _derived_claim(
            claim_id=PROXY_COVERAGE_CLAIM_ID,
            field="proxy_coverage",
            value=values["proxy_coverage"],
            unit=None,
            input_claim_ids=(REQUIRED_INPUT_CLAIM_ID,),
            steps=(values["proxy_coverage_step"],),
        ),
        _derived_claim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="c_pack_final_emission_tco2e",
            value=values["final_emission_tco2e"],
            unit="tCO2e",
            input_claim_ids=(
                OWN_EMISSION_CLAIM_ID,
                ALPHA_CHILD_CLAIM_ID,
                STEEL_PROXY_CHILD_CLAIM_ID,
            ),
            reference_binding_ids=(ELECTRICITY_BINDING_ID,),
            steps=(
                values["required_input_step"],
                values["own_emission_step"],
                values["lower_tier_rollup_step"],
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
        origin="c_pack_rollup_calculated",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _calculated_values() -> dict[str, object]:
    required_input = Decimal(HOUSING_OUTPUT_TON) * (Decimal("1") + SCRAP_LOSS_RATE)
    own_emission = Decimal(ASSEMBLY_ELECTRICITY_MWH) * ELECTRICITY_FACTOR_TCO2E_PER_MWH
    lower_tier_rollup = Decimal(ALPHA_METAL_EMISSION_TCO2E) + Decimal(
        STEEL_FRAME_PROXY_EMISSION_TCO2E
    )
    final_emission = own_emission + lower_tier_rollup
    verified_coverage = Decimal(ALPHA_METAL_INPUT_TON) / required_input
    proxy_coverage = Decimal(MISSING_STEEL_INPUT_TON) / required_input

    return {
        "required_lower_tier_input_ton": _number(required_input),
        "own_emission_tco2e": _number(own_emission),
        "lower_tier_rollup_tco2e": _number(lower_tier_rollup),
        "verified_primary_coverage": _round_3(verified_coverage),
        "proxy_coverage": _round_3(proxy_coverage),
        "final_emission_tco2e": _number(final_emission),
        "required_input_step": CalculationStep(
            step_id="required-lower-tier-input-ton",
            operation="multiply",
            input_ids=("housing_output_ton", "scrap_loss_rate"),
            output_value=_number(required_input),
            output_unit="ton",
        ),
        "own_emission_step": CalculationStep(
            step_id="c-pack-own-emission-tco2e",
            operation="multiply",
            input_ids=("assembly_electricity_mwh", ELECTRICITY_BINDING_ID),
            output_value=_number(own_emission),
            output_unit="tCO2e",
        ),
        "lower_tier_rollup_step": CalculationStep(
            step_id="lower-tier-rollup-tco2e",
            operation="sum",
            input_ids=(ALPHA_CHILD_CLAIM_ID, STEEL_PROXY_CHILD_CLAIM_ID),
            output_value=_number(lower_tier_rollup),
            output_unit="tCO2e",
        ),
        "verified_coverage_step": CalculationStep(
            step_id="verified-primary-coverage",
            operation="divide",
            input_ids=("alpha_metal_input_ton", REQUIRED_INPUT_CLAIM_ID),
            output_value=_round_3(verified_coverage),
        ),
        "proxy_coverage_step": CalculationStep(
            step_id="proxy-coverage",
            operation="divide",
            input_ids=("missing_steel_input_ton", REQUIRED_INPUT_CLAIM_ID),
            output_value=_round_3(proxy_coverage),
        ),
        "final_emission_step": CalculationStep(
            step_id="final-emission-tco2e",
            operation="sum",
            input_ids=(OWN_EMISSION_CLAIM_ID, LOWER_TIER_ROLLUP_CLAIM_ID),
            output_value=_number(final_emission),
            output_unit="tCO2e",
        ),
    }


def _projection_source(report: ValidationReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values


def _round_3(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


C_PACK_YIELD_ROLLUP_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="C-Pack yield-based lower-tier roll-up",
    run=run_c_pack_yield_rollup_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_requirement_kinds=(
            "child_claims_available",
            "proxy_dependency_preserved",
        ),
        required_reference_binding_ids=(ELECTRICITY_BINDING_ID,),
        required_derived_claim_ids=(
            REQUIRED_INPUT_CLAIM_ID,
            OWN_EMISSION_CLAIM_ID,
            LOWER_TIER_ROLLUP_CLAIM_ID,
            VERIFIED_PRIMARY_COVERAGE_CLAIM_ID,
            PROXY_COVERAGE_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(ELECTRICITY_BINDING_ID,),
        required_receipt_derived_claim_ids=(
            REQUIRED_INPUT_CLAIM_ID,
            OWN_EMISSION_CLAIM_ID,
            LOWER_TIER_ROLLUP_CLAIM_ID,
            VERIFIED_PRIMARY_COVERAGE_CLAIM_ID,
            PROXY_COVERAGE_CLAIM_ID,
            FINAL_EMISSION_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{REQUIRED_INPUT_CLAIM_ID}",
            f"trace:{OWN_EMISSION_CLAIM_ID}",
            f"trace:{LOWER_TIER_ROLLUP_CLAIM_ID}",
            f"trace:{VERIFIED_PRIMARY_COVERAGE_CLAIM_ID}",
            f"trace:{PROXY_COVERAGE_CLAIM_ID}",
            f"trace:{FINAL_EMISSION_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "ALPHA_CHILD_CLAIM_ID",
    "C_PACK_YIELD_ROLLUP_SCENARIO",
    "ELECTRICITY_BINDING_ID",
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "PROXY_DEPENDENCY_OBLIGATION_ID",
    "SCENARIO_ID",
    "STEEL_PROXY_CHILD_CLAIM_ID",
    "c_pack_yield_rollup_report",
    "run_c_pack_yield_rollup_scenario",
]
