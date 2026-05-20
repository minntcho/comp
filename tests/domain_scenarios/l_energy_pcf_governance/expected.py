from tests.domain_scenarios.core import SourceRef


SCENARIO_ID = "l_energy_pcf_governance.v1"
SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"

EXPECTED_SOURCE_REFS = (
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

EXPECTED_PROJECTION = {
    "case_id": SOURCE_CASE_ID,
    "total_emission_tco2e": 199994,
    "packs": 100000,
    "total_energy_gwh": 7.5,
    "kgco2e_per_pack": 1999.94,
    "kgco2e_per_kwh": 26.66,
}

EXPECTED_REFERENCE_BINDING_IDS = (
    "bind:pcf:electricity_factor",
    "bind:pcf:lng_factor",
    "bind:pcf:steel_proxy_factor",
    "bind:pcf:carbon_tech_certificate_factor",
    "bind:pcf:ncm811_factor",
)

EXPECTED_REFERENCE_CANDIDATE_IDS = (
    "platform.factor.electricity_mwh",
    "platform.factor.electricity_mwh_2024",
)

EXPECTED_RESOLVED_OBLIGATION_KINDS = (
    "reference_search_required",
    "calculation_blocked",
)

EXPECTED_DERIVED_CLAIM_IDS = (
    "l-energy:own_emission_tco2e",
    "alpha-metal:final_emission_tco2e",
    "steel-frame:final_emission_tco2e",
    "carbon-tech:final_emission_tco2e",
    "l-materials:final_emission_tco2e",
    "c-pack:final_emission_tco2e",
    "l-energy:total_emission_tco2e",
    "l-energy:kgco2e_per_pack",
    "l-energy:kgco2e_per_kwh",
)

EXPECTED_TRACE_IDS = tuple(
    f"trace:{claim_id}" for claim_id in EXPECTED_DERIVED_CLAIM_IDS
)

EXPECTED_FORMULA_IDS = ("pcf-demo-2025.0",)

__all__ = [
    "EXPECTED_DERIVED_CLAIM_IDS",
    "EXPECTED_FORMULA_IDS",
    "EXPECTED_PROJECTION",
    "EXPECTED_REFERENCE_CANDIDATE_IDS",
    "EXPECTED_REFERENCE_BINDING_IDS",
    "EXPECTED_RESOLVED_OBLIGATION_KINDS",
    "EXPECTED_SOURCE_REFS",
    "EXPECTED_TRACE_IDS",
    "SCENARIO_ID",
    "SOURCE_CASE_ID",
]
