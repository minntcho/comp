from __future__ import annotations

from comp.compiler_tool import (
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    ReferenceBinding,
)
from tests.domain_scenarios.l_energy_pcf_governance.expected import (
    SCENARIO_ID,
    SOURCE_CASE_ID,
)


SUBJECT_ID = f"case:{SOURCE_CASE_ID}"
PUBLIC_ROW_ID = f"public-row:{SOURCE_CASE_ID}"
PROFILE_ID = "pcf-governance-platform-fixture-v1"
FORMULA_ID = "pcf-demo-2025.0"


def checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            field="case_id",
            value=SOURCE_CASE_ID,
            witness_id="source:e2e-case-yaml",
            origin="source_ref",
        ),
        CheckedClaim(
            field="packs",
            value=100000,
            witness_id="source:e2e-case-yaml",
            origin="source_ref",
        ),
        CheckedClaim(
            field="total_energy_gwh",
            value=7.5,
            witness_id="source:e2e-case-yaml",
            origin="source_ref",
        ),
    )


def reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id="bind:pcf:electricity_factor",
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.electricity_mwh",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
        ReferenceBinding(
            binding_id="bind:pcf:lng_factor",
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.lng_nm3",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
        ReferenceBinding(
            binding_id="bind:pcf:steel_proxy_factor",
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.steel_proxy_per_ton",
            reference_type="emission_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:dummy-data-mapping",),
        ),
        ReferenceBinding(
            binding_id="bind:pcf:carbon_tech_certificate_factor",
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.carbon_tech_certificate_per_ton",
            reference_type="certificate_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:expected-receipt",),
        ),
        ReferenceBinding(
            binding_id="bind:pcf:ncm811_factor",
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.ncm811_composition",
            reference_type="composition_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:expected-receipt",),
        ),
    )


def derived_claims() -> tuple[DerivedClaim, ...]:
    return (
        _derived_claim(
            claim_id="l-energy:own_emission_tco2e",
            field="l_energy_own_emission_tco2e",
            value=1695,
            reference_binding_ids=(
                "bind:pcf:electricity_factor",
                "bind:pcf:lng_factor",
            ),
        ),
        _derived_claim(
            claim_id="alpha-metal:final_emission_tco2e",
            field="alpha_metal_final_emission_tco2e",
            value=5306,
            reference_binding_ids=(
                "bind:pcf:electricity_factor",
                "bind:pcf:lng_factor",
            ),
        ),
        _derived_claim(
            claim_id="steel-frame:final_emission_tco2e",
            field="steel_frame_final_emission_tco2e",
            value=4750,
            reference_binding_ids=("bind:pcf:steel_proxy_factor",),
        ),
        _derived_claim(
            claim_id="carbon-tech:final_emission_tco2e",
            field="carbon_tech_final_emission_tco2e",
            value=13390,
            reference_binding_ids=("bind:pcf:carbon_tech_certificate_factor",),
        ),
        _derived_claim(
            claim_id="l-materials:final_emission_tco2e",
            field="l_materials_final_emission_tco2e",
            value=174375,
            reference_binding_ids=("bind:pcf:ncm811_factor",),
        ),
        _derived_claim(
            claim_id="c-pack:final_emission_tco2e",
            field="c_pack_final_emission_tco2e",
            value=10534,
            input_claim_ids=(
                "alpha-metal:final_emission_tco2e",
                "steel-frame:final_emission_tco2e",
            ),
            reference_binding_ids=("bind:pcf:electricity_factor",),
        ),
        _derived_claim(
            claim_id="l-energy:total_emission_tco2e",
            field="total_emission_tco2e",
            value=199994,
            input_claim_ids=(
                "l-energy:own_emission_tco2e",
                "c-pack:final_emission_tco2e",
                "carbon-tech:final_emission_tco2e",
                "l-materials:final_emission_tco2e",
            ),
        ),
        _derived_claim(
            claim_id="l-energy:kgco2e_per_pack",
            field="kgco2e_per_pack",
            value=1999.94,
            input_claim_ids=("l-energy:total_emission_tco2e",),
        ),
        _derived_claim(
            claim_id="l-energy:kgco2e_per_kwh",
            field="kgco2e_per_kwh",
            value=26.66,
            input_claim_ids=("l-energy:kgco2e_per_pack",),
        ),
    )


def compile_report() -> CompileReport:
    return CompileReport(
        status="accepted",
        checked_claims=checked_claims(),
        reference_bindings=reference_bindings(),
        derived_claims=derived_claims(),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value: float | int,
    input_claim_ids: tuple[str, ...] = (),
    reference_binding_ids: tuple[str, ...] = (),
) -> DerivedClaim:
    return DerivedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit="tCO2e" if field.endswith("_tco2e") else None,
        origin="fixture_derived",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
        ),
    )


__all__ = [
    "FORMULA_ID",
    "PROFILE_ID",
    "PUBLIC_ROW_ID",
    "SUBJECT_ID",
    "checked_claims",
    "compile_report",
    "derived_claims",
    "reference_bindings",
]
