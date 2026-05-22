from __future__ import annotations

from decimal import Decimal

from comp import SubjectRef
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    ClaimCandidate,
    ValidationReport,
    CalculatedClaim,
    EvidenceRef,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
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


SCENARIO_ID = "synthetic.raw_claim_conflict.v1"
SUBJECT_ID = "case:synthetic-raw-claim-conflict"
PUBLIC_ROW_ID = "public-row:synthetic-raw-claim-conflict"
PROJECTION_ID = "synthetic-raw-claim-conflict"
PROFILE_ID = "profile:synthetic-raw-claim-conflict:v1"

FORMULA_ID = "synthetic.raw_claim_conflict.source_canonicalization.v1"
ALIAS_BINDING_ID = "bind:raw-conflict:site_alias"
PERIOD_BINDING_ID = "bind:raw-conflict:period_policy"
UNIT_CONVERSION_BINDING_ID = "bind:raw-conflict:gwh_to_mwh"
EMAIL_ELECTRICITY_CLAIM_ID = "raw-conflict:email_electricity_mwh"
EMS_ELECTRICITY_CLAIM_ID = "raw-conflict:ems_electricity_mwh"
CONFLICT_OBLIGATION_ID = "raw-conflict:electricity_mwh:source_value_conflict"
CONFLICT_HAZARD_ID = "hazard:source_value_conflict:electricity_mwh:block"

EXPECTED_OPEN_OBLIGATION_IDS = (CONFLICT_OBLIGATION_ID,)
EXPECTED_HAZARD_IDS = (CONFLICT_HAZARD_ID,)

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
    "detect_source_value_conflict",
    "prepare_commit",
    "receipt_blocked_by_source_conflict",
    "no_winner_selected_without_conflict_resolution",
)


def raw_conflict_hypothesis() -> InterpretationHypothesis:
    return InterpretationHypothesis(
        hypothesis_id=SUBJECT_ID,
        subject_id=SUBJECT_ID,
        claims=(
            ClaimCandidate(
                field="site_id",
                value="OCH-01",
                witness_id="w-email-electricity-march",
                origin="llm_extractor_candidate",
            ),
            ClaimCandidate(
                field="period",
                value="2025-03",
                witness_id="w-email-electricity-march",
                origin="llm_extractor_candidate",
            ),
            ClaimCandidate(
                field="electricity",
                value={"amount": 6.4, "unit": "GWh", "source": "email"},
                witness_id="w-email-electricity-march",
                origin="llm_extractor_candidate",
            ),
            ClaimCandidate(
                field="electricity",
                value={"amount": 6.1, "unit": "GWh", "source": "ems"},
                witness_id="w-ems-electricity-march",
                origin="parser_candidate",
            ),
        ),
        witnesses=_evidence_refs()[:2],
    )


def run_raw_claim_conflict_scenario() -> DomainScenarioResult:
    report = raw_claim_conflict_report()
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
    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=None,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def raw_claim_conflict_report() -> ValidationReport:
    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=_evidence_refs(),
            checked_claims=_checked_claims(),
            failed_claims=_failed_claims(),
            resolved_validation_requirements=_resolved_validation_requirements(),
            validation_requirements=_open_obligations(),
            hazards=_hazards(),
            canonical_references=_canonical_references(),
            calculated_claims=_calculated_claims(),
            can_build_public_output=False,
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
            source="profile:synthetic-raw-claim-conflict",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        EvidenceRef(
            witness_id="w-reporting-period-policy",
            field="period",
            source="profile:synthetic-raw-claim-conflict",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        EvidenceRef(
            witness_id="w-unit-conversion-policy",
            field="unit_conversion",
            source="profile:synthetic-raw-claim-conflict",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
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
    )


def _failed_claims() -> tuple[FailedClaim, ...]:
    return (
        FailedClaim(
            field="electricity_mwh",
            value={
                "email_electricity_mwh": 6400,
                "ems_electricity_mwh": 6100,
            },
            reason="source_value_conflict",
            origin="conflict_detection",
            witness_id=None,
        ),
    )


def _resolved_validation_requirements() -> tuple[ValidationRequirement, ...]:
    return (
        ValidationRequirement(
            kind="site_alias_resolved",
            field="site_id",
            reason="OCH-01_alias_bound_to_ocheong_plant_1",
            obligation_id="raw-conflict:site_alias:resolved",
        ),
        ValidationRequirement(
            kind="period_validated",
            field="period",
            reason="period_inside_active_reporting_window",
            obligation_id="raw-conflict:period:validated",
        ),
        ValidationRequirement(
            kind="unit_conversion_policy_applied",
            field="electricity_mwh",
            reason="GWh_to_MWh_conversion_factor_1000",
            obligation_id="raw-conflict:unit_conversion:applied",
        ),
    )


def _open_obligations() -> tuple[ValidationRequirement, ...]:
    return (
        ValidationRequirement(
            kind="resolve_source_conflict",
            field="electricity_mwh",
            reason="email_and_ems_values_disagree_after_canonicalization",
            obligation_id=CONFLICT_OBLIGATION_ID,
        ),
    )


def _hazards() -> tuple[Hazard, ...]:
    return (
        Hazard(
            kind="source_value_conflict",
            field="electricity_mwh",
            severity="block",
        ),
    )


def _canonical_references() -> tuple[CanonicalReference, ...]:
    return (
        CanonicalReference(
            binding_id=ALIAS_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="site-alias:OCH-01->ocheong_plant_1",
            reference_type="site_alias",
            selector_rule_id="synthetic.raw_claim_conflict.fixture",
            source_witness_ids=("w-site-alias-policy",),
        ),
        CanonicalReference(
            binding_id=PERIOD_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="reporting-period:2025-03",
            reference_type="period_policy",
            selector_rule_id="synthetic.raw_claim_conflict.fixture",
            source_witness_ids=("w-reporting-period-policy",),
        ),
        CanonicalReference(
            binding_id=UNIT_CONVERSION_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="unit-conversion:GWh_to_MWh",
            reference_type="unit_conversion",
            selector_rule_id="synthetic.raw_claim_conflict.fixture",
            source_witness_ids=("w-unit-conversion-policy",),
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
            formula_id=FORMULA_ID,
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


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


RAW_CLAIM_CONFLICT_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic raw claim source conflict",
    run=run_raw_claim_conflict_scenario,
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=False,
        required_resolved_obligation_kinds=(
            "site_alias_resolved",
            "period_validated",
            "unit_conversion_policy_applied",
        ),
        required_reference_binding_ids=(
            ALIAS_BINDING_ID,
            PERIOD_BINDING_ID,
            UNIT_CONVERSION_BINDING_ID,
        ),
        required_derived_claim_ids=(
            EMAIL_ELECTRICITY_CLAIM_ID,
            EMS_ELECTRICITY_CLAIM_ID,
        ),
        required_open_obligation_ids=EXPECTED_OPEN_OBLIGATION_IDS,
        required_hazard_ids=EXPECTED_HAZARD_IDS,
    ),
)


__all__ = [
    "ALIAS_BINDING_ID",
    "EMAIL_ELECTRICITY_CLAIM_ID",
    "EMS_ELECTRICITY_CLAIM_ID",
    "EXPECTED_HAZARD_IDS",
    "EXPECTED_OPEN_OBLIGATION_IDS",
    "PERIOD_BINDING_ID",
    "RAW_CLAIM_CONFLICT_SCENARIO",
    "SCENARIO_ID",
    "UNIT_CONVERSION_BINDING_ID",
    "raw_claim_conflict_report",
    "raw_conflict_hypothesis",
    "run_raw_claim_conflict_scenario",
]
