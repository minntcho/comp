from __future__ import annotations

import re

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    ClaimHypothesis,
    CompileReport,
    CompilerTool,
    EvidenceWitness,
    EmbeddingResolverStub,
    InterpretationHypothesis,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceIndexEntry,
    ReferenceQuery,
    ReferenceRecord,
    ReferenceSelectionCriteria,
    apply_calculation_result,
    calculate_derived_claim,
)


SCENARIO_ID = "canonical_working_loop.raw_text_pcf.v1"
SUBJECT_ID = "product:canonical-raw-pcf-1"
PUBLIC_ROW_ID = "public-row:canonical-raw-pcf-1"
PROFILE_ID = "pcf-canonical-loop-v1"
INPUT_CLAIM_ID = "canonical-raw:electricity_kwh"
OUTPUT_CLAIM_ID = "canonical-raw:co2e_kg"
RAW_EVIDENCE = "Seoul office used 1200kWh electricity in Jan 2024."


def extract_raw_evidence(raw_text: str) -> InterpretationHypothesis:
    amount = _required_int(raw_text, r"(\d+)\s*kwh")
    year = _required_int(raw_text, r"(20\d{2})")
    source = "raw-evidence:canonical-working-loop"

    return InterpretationHypothesis(
        hypothesis_id="hyp:canonical-raw-pcf",
        subject_id=SUBJECT_ID,
        claims=(
            ClaimHypothesis("activity", "electricity", witness_id="w-activity"),
            ClaimHypothesis(
                "electricity_kwh",
                amount,
                witness_id="w-electricity-kwh",
                origin="deterministic_extractor",
            ),
            ClaimHypothesis("unit", "kWh", witness_id="w-unit"),
            ClaimHypothesis("reporting_year", year, witness_id="w-reporting-year"),
            ClaimHypothesis("geography", "KR", witness_id="w-geography"),
        ),
        witnesses=(
            EvidenceWitness(
                "w-activity",
                "activity",
                source=source,
                span="electricity",
                text=raw_text,
            ),
            EvidenceWitness(
                "w-electricity-kwh",
                "electricity_kwh",
                source=source,
                span="1200kWh",
                text=raw_text,
            ),
            EvidenceWitness(
                "w-unit",
                "unit",
                source=source,
                span="kWh",
                text=raw_text,
            ),
            EvidenceWitness(
                "w-reporting-year",
                "reporting_year",
                source=source,
                span="2024",
                text=raw_text,
            ),
            EvidenceWitness(
                "w-geography",
                "geography",
                source=source,
                span="Seoul",
                text=raw_text,
            ),
        ),
    )


def compile_raw_evidence(raw_text: str) -> CompileReport:
    return CompilerTool(
        known_fields=frozenset(
            {
                "activity",
                "electricity_kwh",
                "unit",
                "reporting_year",
                "geography",
            }
        )
    ).compile_interpretation(extract_raw_evidence(raw_text))


def open_calculation_obligation(report: CompileReport) -> CompileReport:
    result = calculate_derived_claim(
        output_claim_id=OUTPUT_CLAIM_ID,
        input_claim=input_claim_from_report(report),
        reference_binding=ReferenceBinding(
            binding_id="bind-canonical-electricity-factor",
            claim_id=INPUT_CLAIM_ID,
            reference_id="pcf.factor.unknown",
            reference_type="emission_factor",
        ),
        catalog=ReferenceCatalog(records=()),
        formula=formula(),
    )
    return apply_calculation_result(
        report,
        result,
        output_claim_id=OUTPUT_CLAIM_ID,
        formula=formula(),
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


def reference_resolver() -> EmbeddingResolverStub:
    return EmbeddingResolverStub(
        entries=(
            ReferenceIndexEntry(
                entry_id="idx-canonical-kr-grid-2024",
                reference_id="pcf.factor.kr_grid_2024.location_based",
                reference_type="emission_factor",
                lens="factor",
                text="Korea grid electricity factor 2024 location based",
                reference_db_version="pcf-reference-catalog-v1",
                index_version="canonical-embedding-stub-v1",
                source="pcf-reference-catalog",
                witness_ids=("factor-row-kr-grid-2024",),
            ),
            ReferenceIndexEntry(
                entry_id="idx-canonical-kr-grid-2023",
                reference_id="pcf.factor.kr_grid_2023.location_based",
                reference_type="emission_factor",
                lens="factor",
                text="Korea grid electricity factor 2023 location based",
                reference_db_version="pcf-reference-catalog-v1",
                index_version="canonical-embedding-stub-v1",
                source="pcf-reference-catalog",
                witness_ids=("factor-row-kr-grid-2023",),
            ),
        )
    )


def reference_query_for_obligation(obligation) -> ReferenceQuery | None:
    if obligation.kind != "reference_search_required":
        return None
    return ReferenceQuery(
        query_id=f"canonical-reference-query:{obligation.obligation_id}",
        text="Korea grid electricity factor 2024",
        lens="factor",
        reference_type="emission_factor",
        source_artifact_ids=(obligation.obligation_id or "reference_search_required",),
    )


def criteria() -> ReferenceSelectionCriteria:
    return ReferenceSelectionCriteria(
        binding_id="bind-canonical-electricity-factor",
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


def formula() -> CalculationFormula:
    return CalculationFormula(
        formula_id="pcf.electricity_factor_multiplication.v1",
        output_field="co2e_kg",
        output_unit="kgCO2e",
    )


def input_claim_from_report(report: CompileReport) -> CalculationInput:
    values = {claim.field: claim.value for claim in report.checked_claims}
    return CalculationInput(
        claim_id=INPUT_CLAIM_ID,
        field="electricity_kwh",
        value=values["electricity_kwh"],
        unit=values["unit"],
    )


def projection_source(report: CompileReport) -> dict[str, object]:
    values: dict[str, object] = {
        claim.field: claim.value for claim in report.checked_claims
    }
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _required_int(text: str, pattern: str) -> int:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match is None:
        raise ValueError(f"raw evidence did not match {pattern!r}")
    return int(match.group(1))


__all__ = [
    "OUTPUT_CLAIM_ID",
    "PROFILE_ID",
    "PUBLIC_ROW_ID",
    "RAW_EVIDENCE",
    "SCENARIO_ID",
    "SUBJECT_ID",
    "catalog",
    "compile_raw_evidence",
    "criteria",
    "extract_raw_evidence",
    "formula",
    "input_claim_from_report",
    "open_calculation_obligation",
    "projection_source",
    "reference_query_for_obligation",
    "reference_resolver",
]
