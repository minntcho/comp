from __future__ import annotations

from decimal import Decimal

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
    ProofObligation,
    ReferenceBinding,
    evidence_witness_fingerprint,
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
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_gate.scenario import (
    raw_claim_hypothesis,
)


SCENARIO_ID = "synthetic.raw_claim_hypothesis_acceptance.v1"
SUBJECT_ID = "case:synthetic-raw-claim-hypothesis-acceptance"
PUBLIC_ROW_ID = "public-row:synthetic-raw-claim-hypothesis-acceptance"
PROJECTION_ID = "synthetic-raw-claim-hypothesis-acceptance"
PROFILE_ID = "profile:synthetic-raw-claim-hypothesis-acceptance:v1"

PROJECTION_FIELDS = (
    "site_id",
    "period",
    "electricity_mwh",
    "allocation_share",
    "allocated_electricity_mwh",
)
EXPECTED_PROJECTION = {
    "site_id": "ocheong_plant_1",
    "period": "2025-03",
    "electricity_mwh": 6400,
    "allocation_share": 0.5,
    "allocated_electricity_mwh": 3200,
}

FORMULA_ID = "synthetic.raw_claim_hypothesis_acceptance.v1"
ALIAS_BINDING_ID = "bind:raw-acceptance:site_alias"
UNIT_CONVERSION_BINDING_ID = "bind:raw-acceptance:gwh_to_mwh"
ALLOCATION_SUPPORT_BINDING_ID = "bind:raw-acceptance:allocation_support"
ELECTRICITY_MWH_CLAIM_ID = "raw-acceptance:electricity_mwh"
ALLOCATION_SHARE_CLAIM_ID = "raw-acceptance:allocation_share"
ALLOCATED_ELECTRICITY_CLAIM_ID = "raw-acceptance:allocated_electricity_mwh"

ALIAS_OBLIGATION_ID = "raw-acceptance:site_alias:resolved"
UNIT_CONVERSION_OBLIGATION_ID = "raw-acceptance:unit_conversion:applied"
PERIOD_OBLIGATION_ID = "raw-acceptance:period:validated"
ALLOCATION_SUPPORT_OBLIGATION_ID = "raw-acceptance:allocation_support:validated"

RAW_ELECTRICITY_GWH = Decimal("6.4")
GWH_TO_MWH_FACTOR = Decimal("1000")
LINE_A_MASS_TON = 50000
TOTAL_LINE_MASS_TON = 100000

RESOLVER_STEPS = (
    "llm_extractor_candidate_fixture",
    "evidence_witness_fingerprint",
    "bind_site_alias_reference",
    "bind_unit_conversion_reference",
    "validate_reporting_period",
    "bind_physical_allocation_support",
    "derive_canonical_electricity_mwh",
    "derive_allocation_share",
    "derive_allocated_electricity",
    "prepare_commit",
    "receipt_gated_projection",
)


def run_raw_claim_hypothesis_acceptance_scenario() -> DomainScenarioResult:
    report = raw_claim_hypothesis_acceptance_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
        profile_id=PROFILE_ID,
        dependency_fingerprints=tuple(
            evidence_witness_fingerprint(witness)
            for witness in report.evidence_witnesses
        ),
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


def raw_claim_hypothesis_acceptance_report() -> CompileReport:
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=_evidence_witnesses(),
            checked_claims=_checked_claims(),
            resolved_obligations=_resolved_obligations(),
            reference_bindings=_reference_bindings(),
            derived_claims=_derived_claims(),
            can_project_public_row=True,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    raw_witnesses = raw_claim_hypothesis().witnesses
    return (
        *raw_witnesses,
        EvidenceWitness(
            witness_id="w-site-alias-policy",
            field="site_alias",
            source="profile:synthetic-raw-claim-acceptance",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        EvidenceWitness(
            witness_id="w-unit-conversion-policy",
            field="unit_conversion",
            source="profile:synthetic-raw-claim-acceptance",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
        ),
        EvidenceWitness(
            witness_id="w-reporting-period-policy",
            field="period",
            source="profile:synthetic-raw-claim-acceptance",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        EvidenceWitness(
            witness_id="w-allocation-support",
            field="allocation_support",
            source="raw_sources/mes_line_mass.csv",
            span="line_mass_row:line_a",
            text="Line A 50,000 ton; total line mass 100,000 ton",
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
            "reporting_period_policy",
        ),
        CheckedClaim(
            "electricity_gwh",
            _number(RAW_ELECTRICITY_GWH),
            "w-email-electricity-march",
            "raw_candidate_with_unit_policy",
        ),
        CheckedClaim(
            "line_a_mass_ton",
            LINE_A_MASS_TON,
            "w-allocation-support",
            "physical_allocation_support",
        ),
        CheckedClaim(
            "total_line_mass_ton",
            TOTAL_LINE_MASS_TON,
            "w-allocation-support",
            "physical_allocation_support",
        ),
    )


def _resolved_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="site_alias_resolved",
            field="site_id",
            reason="OCH-01_alias_bound_to_ocheong_plant_1",
            obligation_id=ALIAS_OBLIGATION_ID,
        ),
        ProofObligation(
            kind="unit_conversion_policy_applied",
            field="electricity_mwh",
            reason="GWh_to_MWh_conversion_factor_1000",
            obligation_id=UNIT_CONVERSION_OBLIGATION_ID,
        ),
        ProofObligation(
            kind="period_validated",
            field="period",
            reason="period_inside_active_reporting_window",
            obligation_id=PERIOD_OBLIGATION_ID,
        ),
        ProofObligation(
            kind="physical_allocation_support_validated",
            field="allocation_share",
            reason="line_a_mass_over_total_line_mass",
            obligation_id=ALLOCATION_SUPPORT_OBLIGATION_ID,
        ),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=ALIAS_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="site-alias:OCH-01->ocheong_plant_1",
            reference_type="site_alias",
            selector_rule_id="synthetic.raw_claim_acceptance.fixture",
            source_witness_ids=("w-site-alias-policy",),
        ),
        ReferenceBinding(
            binding_id=UNIT_CONVERSION_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="unit-conversion:GWh_to_MWh",
            reference_type="unit_conversion",
            selector_rule_id="synthetic.raw_claim_acceptance.fixture",
            source_witness_ids=("w-unit-conversion-policy",),
        ),
        ReferenceBinding(
            binding_id=ALLOCATION_SUPPORT_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="physical-allocation-support:line_a_mass_share",
            reference_type="physical_allocation_support",
            selector_rule_id="synthetic.raw_claim_acceptance.fixture",
            source_witness_ids=("w-allocation-support",),
        ),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    values = _calculated_values()
    return (
        _derived_claim(
            claim_id=ELECTRICITY_MWH_CLAIM_ID,
            field="electricity_mwh",
            value=values["electricity_mwh"],
            unit="MWh",
            input_claim_ids=("electricity_gwh",),
            reference_binding_ids=(UNIT_CONVERSION_BINDING_ID,),
            steps=(values["unit_conversion_step"],),
        ),
        _derived_claim(
            claim_id=ALLOCATION_SHARE_CLAIM_ID,
            field="allocation_share",
            value=values["allocation_share"],
            unit=None,
            input_claim_ids=("line_a_mass_ton", "total_line_mass_ton"),
            reference_binding_ids=(ALLOCATION_SUPPORT_BINDING_ID,),
            steps=(values["allocation_share_step"],),
        ),
        _derived_claim(
            claim_id=ALLOCATED_ELECTRICITY_CLAIM_ID,
            field="allocated_electricity_mwh",
            value=values["allocated_electricity_mwh"],
            unit="MWh",
            input_claim_ids=(ELECTRICITY_MWH_CLAIM_ID, ALLOCATION_SHARE_CLAIM_ID),
            reference_binding_ids=(
                UNIT_CONVERSION_BINDING_ID,
                ALLOCATION_SUPPORT_BINDING_ID,
            ),
            steps=(values["allocated_electricity_step"],),
        ),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value,
    unit: str | None,
    input_claim_ids: tuple[str, ...],
    reference_binding_ids: tuple[str, ...],
    steps: tuple[CalculationStep, ...],
) -> DerivedClaim:
    return DerivedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin="raw_claim_hypothesis_acceptance_calculated",
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=FORMULA_ID,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _calculated_values() -> dict[str, object]:
    electricity_mwh = RAW_ELECTRICITY_GWH * GWH_TO_MWH_FACTOR
    allocation_share = Decimal(LINE_A_MASS_TON) / Decimal(TOTAL_LINE_MASS_TON)
    allocated_electricity = electricity_mwh * allocation_share

    return {
        "electricity_mwh": _number(electricity_mwh),
        "allocation_share": _number(allocation_share),
        "allocated_electricity_mwh": _number(allocated_electricity),
        "unit_conversion_step": CalculationStep(
            step_id="convert-gwh-to-mwh",
            operation="multiply",
            input_ids=("electricity_gwh", UNIT_CONVERSION_BINDING_ID),
            output_value=_number(electricity_mwh),
            output_unit="MWh",
        ),
        "allocation_share_step": CalculationStep(
            step_id="line-a-allocation-share",
            operation="divide",
            input_ids=("line_a_mass_ton", "total_line_mass_ton"),
            output_value=_number(allocation_share),
        ),
        "allocated_electricity_step": CalculationStep(
            step_id="allocated-electricity-mwh",
            operation="multiply",
            input_ids=(ELECTRICITY_MWH_CLAIM_ID, ALLOCATION_SHARE_CLAIM_ID),
            output_value=_number(allocated_electricity),
            output_unit="MWh",
        ),
    }


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Synthetic raw ClaimHypothesis acceptance",
    run=run_raw_claim_hypothesis_acceptance_scenario,
    source_refs=(
        SourceRef(
            repo="minntcho/comp",
            path="comp/scenarios/synthetic",
        ),
    ),
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=(
            "site_alias_resolved",
            "unit_conversion_policy_applied",
            "period_validated",
            "physical_allocation_support_validated",
        ),
        required_reference_binding_ids=(
            ALIAS_BINDING_ID,
            UNIT_CONVERSION_BINDING_ID,
            ALLOCATION_SUPPORT_BINDING_ID,
        ),
        required_derived_claim_ids=(
            ELECTRICITY_MWH_CLAIM_ID,
            ALLOCATION_SHARE_CLAIM_ID,
            ALLOCATED_ELECTRICITY_CLAIM_ID,
        ),
        required_receipt_reference_binding_ids=(
            ALIAS_BINDING_ID,
            UNIT_CONVERSION_BINDING_ID,
            ALLOCATION_SUPPORT_BINDING_ID,
        ),
        required_receipt_derived_claim_ids=(
            ELECTRICITY_MWH_CLAIM_ID,
            ALLOCATION_SHARE_CLAIM_ID,
            ALLOCATED_ELECTRICITY_CLAIM_ID,
        ),
        required_receipt_calculation_trace_ids=(
            f"trace:{ELECTRICITY_MWH_CLAIM_ID}",
            f"trace:{ALLOCATION_SHARE_CLAIM_ID}",
            f"trace:{ALLOCATED_ELECTRICITY_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "ALIAS_BINDING_ID",
    "ALLOCATED_ELECTRICITY_CLAIM_ID",
    "ALLOCATION_SHARE_CLAIM_ID",
    "ALLOCATION_SUPPORT_BINDING_ID",
    "ELECTRICITY_MWH_CLAIM_ID",
    "EXPECTED_PROJECTION",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "RAW_CLAIM_HYPOTHESIS_ACCEPTANCE_SCENARIO",
    "SCENARIO_ID",
    "UNIT_CONVERSION_BINDING_ID",
    "raw_claim_hypothesis",
    "raw_claim_hypothesis_acceptance_report",
    "run_raw_claim_hypothesis_acceptance_scenario",
]
