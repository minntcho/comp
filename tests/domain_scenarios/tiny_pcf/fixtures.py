from __future__ import annotations

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CheckedClaim,
    CompileReport,
    CompilerProfile,
    DomainPack,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    RuleFamily,
    apply_calculation_result,
    calculate_derived_claim,
)


SCENARIO_ID = "tiny_pcf.location_based_electricity.v1"
SUBJECT_ID = "product:tiny-pcf-1"
PUBLIC_ROW_ID = "public-row:tiny-pcf-1"
PROFILE_ID = "pcf-lca-lab-v1"
INPUT_CLAIM_ID = "tiny-pcf:electricity_kwh"
OUTPUT_CLAIM_ID = "tiny-pcf:co2e_kg"


def profile() -> CompilerProfile:
    return CompilerProfile(
        profile_id=PROFILE_ID,
        domain_packs=(
            DomainPack(
                domain_id="pcf-lca-lab",
                version="2026.1",
                rule_families=(
                    RuleFamily(
                        rule_id="pcf.factor_selector.v1",
                        description=(
                            "Select a location-based electricity factor by "
                            "concept, geography, period, and method."
                        ),
                    ),
                ),
            ),
        ),
        active_rule_ids=("pcf.factor_selector.v1",),
        projection_policy_id="pcf.public-row.v1",
    )


def catalog() -> ReferenceCatalog:
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="pcf.factor.kr_grid_2024.location_based",
                reference_type="emission_factor",
                labels=("Korea grid electricity factor 2024",),
                aliases=("KR electricity grid factor",),
                description=(
                    "Location-based electricity emission factor for Korea in 2024."
                ),
                attributes=(
                    ("concept_id", "pcf.concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                    ("factor_value", 0.42),
                    ("input_unit", "kWh"),
                    ("output_unit", "kgCO2e"),
                ),
                source="pcf-reference-catalog",
                witness_ids=("factor-row-kr-grid-2024",),
            ),
            ReferenceRecord(
                reference_id="pcf.factor.kr_grid_2023.location_based",
                reference_type="emission_factor",
                labels=("Korea grid electricity factor 2023",),
                aliases=("KR electricity grid factor historical",),
                description=(
                    "Location-based electricity emission factor for Korea in 2023."
                ),
                attributes=(
                    ("concept_id", "pcf.concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2023"),
                    ("method", "location_based"),
                    ("factor_value", 0.41),
                    ("input_unit", "kWh"),
                    ("output_unit", "kgCO2e"),
                ),
                source="pcf-reference-catalog",
                witness_ids=("factor-row-kr-grid-2023",),
            ),
        )
    )


def input_claim() -> CalculationInput:
    return CalculationInput(
        claim_id=INPUT_CLAIM_ID,
        field="electricity_kwh",
        value=1200,
        unit="kWh",
    )


def formula() -> CalculationFormula:
    return CalculationFormula(
        formula_id="pcf.electricity_factor_multiplication.v1",
        output_field="co2e_kg",
        output_unit="kgCO2e",
    )


def criteria() -> ReferenceSelectionCriteria:
    return ReferenceSelectionCriteria(
        binding_id="bind-electricity-factor",
        claim_id=INPUT_CLAIM_ID,
        reference_type="emission_factor",
        selector_rule_id="pcf.factor_selector.v1",
        required_attributes=(
            ("concept_id", "pcf.concept.electricity_consumption"),
            ("geography", "KR"),
            ("valid_period", "2024"),
            ("method", "location_based"),
        ),
    )


def blocked_report() -> CompileReport:
    result = calculate_derived_claim(
        output_claim_id=OUTPUT_CLAIM_ID,
        input_claim=input_claim(),
        reference_binding=ReferenceBinding(
            binding_id="bind-electricity-factor",
            claim_id=INPUT_CLAIM_ID,
            reference_id="pcf.factor.unknown",
            reference_type="emission_factor",
        ),
        catalog=ReferenceCatalog(records=()),
        formula=formula(),
    )
    return apply_calculation_result(
        CompileReport(
            status="accepted",
            checked_claims=(
                CheckedClaim(
                    field="electricity_kwh",
                    value=1200,
                    witness_id="span-electricity-amount",
                    origin="source_text",
                ),
            ),
        ),
        result,
        output_claim_id=OUTPUT_CLAIM_ID,
        formula=formula(),
    )


__all__ = [
    "OUTPUT_CLAIM_ID",
    "PROFILE_ID",
    "PUBLIC_ROW_ID",
    "SCENARIO_ID",
    "SUBJECT_ID",
    "blocked_report",
    "catalog",
    "criteria",
    "formula",
    "input_claim",
    "profile",
]
