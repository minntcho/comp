from __future__ import annotations

from decimal import Decimal

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
    evidence_ref_fingerprint,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "synthetic.raw_claim_conflict_resolution.v1"
SUBJECT_ID = "case:synthetic-raw-claim-conflict-resolution"
PUBLIC_ROW_ID = "public-row:synthetic-raw-claim-conflict-resolution"
PROJECTION_ID = "synthetic-raw-claim-conflict-resolution"
PROFILE_ID = "profile:synthetic-raw-claim-conflict-resolution:v1"

PROJECTION_FIELDS = (
    "site_id",
    "period",
    "electricity_mwh",
    "selected_electricity_source",
)
EXPECTED_PROJECTION = {
    "site_id": "ocheong_plant_1",
    "period": "2025-03",
    "electricity_mwh": 6100,
    "selected_electricity_source": "ems",
}

SOURCE_FORMULA_ID = (
    "synthetic.raw_claim_conflict_resolution.source_canonicalization.v1"
)
RESOLUTION_FORMULA_ID = (
    "synthetic.raw_claim_conflict_resolution.source_selection.v1"
)
ALIAS_BINDING_ID = "bind:raw-conflict-resolution:site_alias"
PERIOD_BINDING_ID = "bind:raw-conflict-resolution:period_policy"
UNIT_CONVERSION_BINDING_ID = "bind:raw-conflict-resolution:gwh_to_mwh"
RESOLUTION_BINDING_ID = "bind:raw-conflict-resolution:source_selection"
EMAIL_ELECTRICITY_CLAIM_ID = (
    "raw-conflict-resolution:email_electricity_mwh"
)
EMS_ELECTRICITY_CLAIM_ID = "raw-conflict-resolution:ems_electricity_mwh"
CANONICAL_ELECTRICITY_CLAIM_ID = (
    "raw-conflict-resolution:electricity_mwh"
)

EMAIL_GWH = Decimal("6.4")
EMS_GWH = Decimal("6.1")
GWH_TO_MWH_FACTOR = Decimal("1000")

RESOLVER_STEPS = (
    "llm_and_parser_candidate_fixture",
    "evidence_ref_fingerprint",
    "bind_site_alias_reference",
    "bind_period_policy",
    "bind_unit_conversion_reference",
    "canonicalize_source_specific_values",
    "source_conflict_resolution_evidence",
    "bind_source_conflict_resolution",
    "select_ems_canonical_electricity_mwh",
    "prepare_commit",
    "receipt_gated_projection",
)


def run_raw_claim_conflict_resolution_scenario() -> DomainScenarioResult:
    report = raw_claim_conflict_resolution_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
        dependency_fingerprints=tuple(
            evidence_ref_fingerprint(witness)
            for witness in report.evidence_refs
        ),
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


def raw_claim_conflict_resolution_report() -> ValidationReport:
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
            witness_id="w-email-electricity-march",
            field="raw_email",
            source="email:synthetic-pcf-smoke:001",
            span="body[0:82]",
            text="March electricity was 6.4 GWh for OCH-01.",
        ),
        EvidenceRef(
            witness_id="w-ems-electricity-march",
            field="raw_ems_export",
            source="raw_sources/ems_electricity.csv",
            span="row:OCH-01:2025-03",
            text="OCH-01,2025-03,6.1,GWh",
        ),
        EvidenceRef(
            witness_id="w-site-alias-policy",
            field="site_alias",
            source="profile:synthetic-raw-claim-conflict-resolution",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        EvidenceRef(
            witness_id="w-reporting-period-policy",
            field="period",
            source="profile:synthetic-raw-claim-conflict-resolution",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        EvidenceRef(
            witness_id="w-unit-conversion-policy",
            field="unit_conversion",
            source="profile:synthetic-raw-claim-conflict-resolution",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
        ),
        EvidenceRef(
            witness_id="w-source-conflict-resolution",
            field="source_conflict_resolution",
            source="resolution_artifacts/source_conflicts.csv",
            span="row:OCH-01:2025-03:electricity",
            text=(
                "Use EMS export for OCH-01 March electricity; "
                "email value is an informal estimate."
            ),
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "site_id",
            "ocheong_plant_1",
            "w-site-alias-policy",
            "site_alias_binding",
        ),
        CheckedClaim(
            "period",
            "2025-03",
            "w-reporting-period-policy",
            "period_policy",
        ),
        CheckedClaim(
            "email_electricity_gwh",
            _number(EMAIL_GWH),
            "w-email-electricity-march",
            "llm_extractor_candidate",
        ),
        CheckedClaim(
            "ems_electricity_gwh",
            _number(EMS_GWH),
            "w-ems-electricity-march",
            "parser_candidate",
        ),
        CheckedClaim(
            "selected_electricity_source",
            "ems",
            "w-source-conflict-resolution",
            "source_conflict_resolution_evidence",
        ),
    )


def _resolved_validation_requirements() -> tuple[ValidationRequirement, ...]:
    return (
        ValidationRequirement(
            kind="site_alias_resolved",
            field="site_id",
            reason="OCH-01_alias_bound_to_ocheong_plant_1",
            requirement_id="raw-conflict-resolution:site_alias:resolved",
        ),
        ValidationRequirement(
            kind="period_validated",
            field="period",
            reason="period_inside_active_reporting_window",
            requirement_id="raw-conflict-resolution:period:validated",
        ),
        ValidationRequirement(
            kind="unit_conversion_policy_applied",
            field="electricity_mwh",
            reason="GWh_to_MWh_conversion_factor_1000",
            requirement_id="raw-conflict-resolution:unit_conversion:applied",
        ),
        ValidationRequirement(
            kind="source_conflict_resolved",
            field="electricity_mwh",
            reason="ems_source_selected_by_resolution_evidence",
            requirement_id="raw-conflict-resolution:electricity_mwh:resolved",
        ),
    )


def _canonical_references() -> tuple[CanonicalReference, ...]:
    return (
        CanonicalReference(
            binding_id=ALIAS_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="site-alias:OCH-01->ocheong_plant_1",
            reference_type="site_alias",
            selector_rule_id="synthetic.raw_claim_conflict_resolution.fixture",
            source_witness_ids=("w-site-alias-policy",),
        ),
        CanonicalReference(
            binding_id=PERIOD_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="reporting-period:2025-03",
            reference_type="period_policy",
            selector_rule_id="synthetic.raw_claim_conflict_resolution.fixture",
            source_witness_ids=("w-reporting-period-policy",),
        ),
        CanonicalReference(
            binding_id=UNIT_CONVERSION_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="unit-conversion:GWh_to_MWh",
            reference_type="unit_conversion",
            selector_rule_id="synthetic.raw_claim_conflict_resolution.fixture",
            source_witness_ids=("w-unit-conversion-policy",),
        ),
        CanonicalReference(
            binding_id=RESOLUTION_BINDING_ID,
            claim_id=CANONICAL_ELECTRICITY_CLAIM_ID,
            reference_id="source-conflict-resolution:ems_export_preferred",
            reference_type="source_conflict_resolution",
            selector_rule_id="synthetic.raw_claim_conflict_resolution.fixture",
            source_witness_ids=(
                "w-source-conflict-resolution",
                "w-ems-electricity-march",
            ),
        ),
    )


def _calculated_claims() -> tuple[CalculatedClaim, ...]:
    email_mwh = EMAIL_GWH * GWH_TO_MWH_FACTOR
    ems_mwh = EMS_GWH * GWH_TO_MWH_FACTOR
    return (
        _source_electricity_claim(
            claim_id=EMAIL_ELECTRICITY_CLAIM_ID,
            field="email_electricity_mwh",
            input_field="email_electricity_gwh",
            output_value=_number(email_mwh),
        ),
        _source_electricity_claim(
            claim_id=EMS_ELECTRICITY_CLAIM_ID,
            field="ems_electricity_mwh",
            input_field="ems_electricity_gwh",
            output_value=_number(ems_mwh),
        ),
        CalculatedClaim(
            claim_id=CANONICAL_ELECTRICITY_CLAIM_ID,
            field="electricity_mwh",
            value=_number(ems_mwh),
            unit="MWh",
            origin="source_conflict_resolution_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{CANONICAL_ELECTRICITY_CLAIM_ID}",
                formula_id=RESOLUTION_FORMULA_ID,
                input_claim_ids=(
                    EMS_ELECTRICITY_CLAIM_ID,
                    "selected_electricity_source",
                ),
                reference_binding_ids=(RESOLUTION_BINDING_ID,),
                steps=(
                    CalculationStep(
                        step_id="select-ems-electricity-mwh",
                        operation="select",
                        input_ids=(
                            EMS_ELECTRICITY_CLAIM_ID,
                            RESOLUTION_BINDING_ID,
                        ),
                        output_value=_number(ems_mwh),
                        output_unit="MWh",
                    ),
                ),
            ),
        ),
    )


def _source_electricity_claim(
    *,
    claim_id: str,
    field: str,
    input_field: str,
    output_value: int | float,
) -> CalculatedClaim:
    return CalculatedClaim(
        claim_id=claim_id,
        field=field,
        value=output_value,
        unit="MWh",
        origin="source_specific_unit_conversion",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=SOURCE_FORMULA_ID,
            input_claim_ids=(input_field,),
            reference_binding_ids=(UNIT_CONVERSION_BINDING_ID,),
            steps=(
                CalculationStep(
                    step_id=f"convert-{input_field}-to-mwh",
                    operation="multiply",
                    input_ids=(input_field, UNIT_CONVERSION_BINDING_ID),
                    output_value=output_value,
                    output_unit="MWh",
                ),
            ),
        ),
    )


def _projection_source(report: ValidationReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic raw claim source conflict resolution",
    run=run_raw_claim_conflict_resolution_scenario,
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_requirement_kinds=(
            "site_alias_resolved",
            "period_validated",
            "unit_conversion_policy_applied",
            "source_conflict_resolved",
        ),
        required_reference_binding_ids=(
            ALIAS_BINDING_ID,
            PERIOD_BINDING_ID,
            UNIT_CONVERSION_BINDING_ID,
            RESOLUTION_BINDING_ID,
        ),
        required_derived_claim_ids=(
            EMAIL_ELECTRICITY_CLAIM_ID,
            EMS_ELECTRICITY_CLAIM_ID,
            CANONICAL_ELECTRICITY_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(
            ALIAS_BINDING_ID,
            PERIOD_BINDING_ID,
            UNIT_CONVERSION_BINDING_ID,
            RESOLUTION_BINDING_ID,
        ),
        required_receipt_derived_claim_ids=(
            EMAIL_ELECTRICITY_CLAIM_ID,
            EMS_ELECTRICITY_CLAIM_ID,
            CANONICAL_ELECTRICITY_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{EMAIL_ELECTRICITY_CLAIM_ID}",
            f"trace:{EMS_ELECTRICITY_CLAIM_ID}",
            f"trace:{CANONICAL_ELECTRICITY_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(SOURCE_FORMULA_ID, RESOLUTION_FORMULA_ID),
    ),
)


__all__ = [
    "CANONICAL_ELECTRICITY_CLAIM_ID",
    "EMAIL_ELECTRICITY_CLAIM_ID",
    "EMS_ELECTRICITY_CLAIM_ID",
    "EXPECTED_PROJECTION",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "RAW_CLAIM_CONFLICT_RESOLUTION_SCENARIO",
    "RESOLUTION_BINDING_ID",
    "SCENARIO_ID",
    "raw_claim_conflict_resolution_report",
    "run_raw_claim_conflict_resolution_scenario",
]
