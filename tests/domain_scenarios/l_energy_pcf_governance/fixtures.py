from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EmbeddingResolverStub,
    ReferenceCatalog,
    ReferenceBinding,
    ReferenceIndexEntry,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    apply_calculation_result,
    calculate_derived_claim,
    with_recomputed_status,
)
from tests.domain_scenarios.l_energy_pcf_governance.expected import (
    SCENARIO_ID,
    SOURCE_CASE_ID,
)


SUBJECT_ID = f"case:{SOURCE_CASE_ID}"
PUBLIC_ROW_ID = f"public-row:{SOURCE_CASE_ID}"
PROFILE_ID = "pcf-governance-platform-fixture-v1"
FORMULA_ID = "pcf-demo-2025.0"
INPUT_CLAIM_ID = "l-energy:total_energy_gwh"
OUTPUT_CLAIM_ID = "l-energy:own_emission_tco2e"
ELECTRICITY_BINDING_ID = "bind:pcf:electricity_factor"


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
            binding_id=ELECTRICITY_BINDING_ID,
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


def downstream_reference_bindings() -> tuple[ReferenceBinding, ...]:
    return tuple(
        binding
        for binding in reference_bindings()
        if binding.binding_id != ELECTRICITY_BINDING_ID
    )


def derived_claims() -> tuple[DerivedClaim, ...]:
    return (
        _derived_claim(
            claim_id=OUTPUT_CLAIM_ID,
            field="l_energy_own_emission_tco2e",
            value=1695,
            reference_binding_ids=(
                ELECTRICITY_BINDING_ID,
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


def downstream_derived_claims() -> tuple[DerivedClaim, ...]:
    return tuple(
        claim for claim in derived_claims() if claim.claim_id != OUTPUT_CLAIM_ID
    )


def blocked_report() -> CompileReport:
    result = calculate_derived_claim(
        output_claim_id=OUTPUT_CLAIM_ID,
        input_claim=input_claim(),
        reference_binding=ReferenceBinding(
            binding_id=ELECTRICITY_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.unresolved_l_energy_energy",
            reference_type="emission_factor",
        ),
        catalog=ReferenceCatalog(records=()),
        formula=formula(),
    )
    return apply_calculation_result(
        CompileReport(status="accepted", checked_claims=checked_claims()),
        result,
        output_claim_id=OUTPUT_CLAIM_ID,
        formula=formula(),
    )


def catalog() -> ReferenceCatalog:
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="platform.factor.electricity_mwh",
                reference_type="emission_factor",
                labels=("L-Energy electricity and LNG factor 2025",),
                aliases=("L-Energy own site energy factor",),
                description=(
                    "Platform fixture factor for L-Energy own energy emissions."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "KR"),
                    ("valid_period", "2025"),
                    ("method", "platform_expected_receipt"),
                    ("factor_value", 226),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping",),
            ),
            ReferenceRecord(
                reference_id="platform.factor.a_supplier_electricity_mwh_2025",
                reference_type="emission_factor",
                labels=("L-Energy supplier specific electricity factor 2025",),
                aliases=("L-Energy electricity LNG factor 2025",),
                description=(
                    "Near-miss platform fixture factor with a supplier-specific "
                    "method instead of the expected platform receipt method."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "KR"),
                    ("valid_period", "2025"),
                    ("method", "supplier_specific"),
                    ("factor_value", 210),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:supplier-near-miss",),
            ),
            ReferenceRecord(
                reference_id="platform.factor.electricity_mwh_2024",
                reference_type="emission_factor",
                labels=("L-Energy electricity and LNG factor 2024",),
                aliases=("L-Energy historical own site energy factor",),
                description=(
                    "Near-miss platform fixture factor with the wrong valid period."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "platform_expected_receipt"),
                    ("factor_value", 220),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:2024-near-miss",),
            ),
            ReferenceRecord(
                reference_id="platform.factor.electricity_residual_mix_2025",
                reference_type="emission_factor",
                labels=("L-Energy residual mix electricity factor 2025",),
                aliases=("Korea L-Energy market-based energy factor",),
                description=(
                    "Near-miss platform fixture factor with the wrong Scope 2 "
                    "method."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "KR"),
                    ("valid_period", "2025"),
                    ("method", "market_based"),
                    ("factor_value", 198),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:residual-mix-near-miss",),
            ),
            ReferenceRecord(
                reference_id="platform.factor.global_average_electricity_mwh_2025",
                reference_type="emission_factor",
                labels=("Global average electricity LNG factor 2025",),
                description=(
                    "Near-miss platform fixture factor with the wrong geography."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "GLOBAL"),
                    ("valid_period", "2025"),
                    ("method", "platform_expected_receipt"),
                    ("factor_value", 300),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:global-near-miss",),
            ),
            ReferenceRecord(
                reference_id="platform.factor.us_electricity_mwh_2025",
                reference_type="emission_factor",
                labels=("US electricity LNG factor 2025",),
                description=(
                    "Near-miss platform fixture factor with a non-KR geography."
                ),
                attributes=(
                    ("concept_id", "platform.concept.l_energy_own_energy"),
                    ("geography", "US"),
                    ("valid_period", "2025"),
                    ("method", "platform_expected_receipt"),
                    ("factor_value", 390),
                    ("input_unit", "GWh"),
                    ("output_unit", "tCO2e"),
                ),
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:us-near-miss",),
            ),
        )
    )


def reference_resolver() -> EmbeddingResolverStub:
    return EmbeddingResolverStub(
        entries=(
            ReferenceIndexEntry(
                entry_id="idx-l-energy-electricity-mwh-2025",
                reference_id="platform.factor.electricity_mwh",
                reference_type="emission_factor",
                lens="factor",
                text="Korea L-Energy electricity LNG factor 2025",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-l-energy-supplier-electricity-mwh-2025",
                reference_id="platform.factor.a_supplier_electricity_mwh_2025",
                reference_type="emission_factor",
                lens="factor",
                text="Korea L-Energy electricity LNG factor 2025",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:supplier-near-miss",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-l-energy-electricity-mwh-2024",
                reference_id="platform.factor.electricity_mwh_2024",
                reference_type="emission_factor",
                lens="factor",
                text="Korea L-Energy electricity LNG factor 2024",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:2024-near-miss",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-l-energy-electricity-residual-mix-2025",
                reference_id="platform.factor.electricity_residual_mix_2025",
                reference_type="emission_factor",
                lens="factor",
                text="Korea L-Energy residual mix electricity factor 2025",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:residual-mix-near-miss",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-l-energy-global-average-electricity-mwh-2025",
                reference_id="platform.factor.global_average_electricity_mwh_2025",
                reference_type="emission_factor",
                lens="factor",
                text="Korea global average electricity LNG factor 2025",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:global-near-miss",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-l-energy-us-electricity-mwh-2025",
                reference_id="platform.factor.us_electricity_mwh_2025",
                reference_type="emission_factor",
                lens="factor",
                text="US electricity LNG factor 2025",
                reference_db_version="l-energy-platform-fixture-v1",
                index_version="l-energy-embedding-stub-v1",
                source="source:dummy-data-mapping",
                witness_ids=("source:dummy-data-mapping:us-near-miss",),
            ),
        )
    )


def retrieval_query_policy() -> RetrievalQueryPolicy:
    return RetrievalQueryPolicy(
        policy_id="l-energy-pcf-retrieval-query-policy-v1",
        rules=(
            RetrievalQueryRule(
                rule_id="l-energy-own-energy-factor-query-v1",
                formula_id=FORMULA_ID,
                lens="factor",
                reference_type="emission_factor",
                text_template=(
                    "{geography} L-Energy electricity LNG factor {reporting_year}"
                ),
            ),
        ),
    )


def retrieval_query_context() -> dict[str, object]:
    return {
        "geography": "Korea",
        "reporting_year": "2025",
    }


def criteria() -> ReferenceSelectionCriteria:
    return ReferenceSelectionCriteria(
        binding_id=ELECTRICITY_BINDING_ID,
        claim_id=SCENARIO_ID,
        reference_type="emission_factor",
        selector_rule_id="pcf.factor_selector.v1",
        required_attributes=(
            ("concept_id", "platform.concept.l_energy_own_energy"),
            ("geography", "KR"),
            ("valid_period", "2025"),
            ("method", "platform_expected_receipt"),
        ),
    )


def input_claim() -> CalculationInput:
    return CalculationInput(
        claim_id=INPUT_CLAIM_ID,
        field="total_energy_gwh",
        value=7.5,
        unit="GWh",
    )


def formula() -> CalculationFormula:
    return CalculationFormula(
        formula_id=FORMULA_ID,
        output_field="l_energy_own_emission_tco2e",
        output_unit="tCO2e",
    )


def attach_downstream_fixture_artifacts(report: CompileReport) -> CompileReport:
    return with_recomputed_status(
        replace(
            report,
            reference_bindings=_append_missing_reference_bindings(
                report.reference_bindings,
                downstream_reference_bindings(),
            ),
            derived_claims=_append_missing_derived_claims(
                report.derived_claims,
                downstream_derived_claims(),
            ),
            can_project_public_row=False,
        )
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


def _append_missing_reference_bindings(
    existing: tuple[ReferenceBinding, ...],
    additions: tuple[ReferenceBinding, ...],
) -> tuple[ReferenceBinding, ...]:
    binding_ids = {binding.binding_id for binding in existing}
    return (
        *existing,
        *(binding for binding in additions if binding.binding_id not in binding_ids),
    )


def _append_missing_derived_claims(
    existing: tuple[DerivedClaim, ...],
    additions: tuple[DerivedClaim, ...],
) -> tuple[DerivedClaim, ...]:
    claim_ids = {claim.claim_id for claim in existing}
    return (
        *existing,
        *(claim for claim in additions if claim.claim_id not in claim_ids),
    )


__all__ = [
    "ELECTRICITY_BINDING_ID",
    "FORMULA_ID",
    "INPUT_CLAIM_ID",
    "OUTPUT_CLAIM_ID",
    "PROFILE_ID",
    "PUBLIC_ROW_ID",
    "SUBJECT_ID",
    "attach_downstream_fixture_artifacts",
    "blocked_report",
    "catalog",
    "checked_claims",
    "compile_report",
    "criteria",
    "derived_claims",
    "downstream_derived_claims",
    "downstream_reference_bindings",
    "formula",
    "input_claim",
    "reference_resolver",
    "reference_bindings",
    "retrieval_query_context",
    "retrieval_query_policy",
]
