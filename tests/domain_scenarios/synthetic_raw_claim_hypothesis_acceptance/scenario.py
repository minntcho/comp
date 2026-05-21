from __future__ import annotations

from decimal import Decimal

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import evidence_witness_fingerprint, prepare_commit
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
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


def raw_claim_hypothesis_acceptance_report():
    return promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )


def _acceptance_profile() -> SyntheticRawClaimPromotionProfile:
    return SyntheticRawClaimPromotionProfile(
        profile_id=PROFILE_ID,
        scenario_id=SCENARIO_ID,
        formula_id=FORMULA_ID,
        selector_rule_id="synthetic.raw_claim_acceptance.fixture",
        claim_ids=PromotionClaimIds(
            electricity_mwh=ELECTRICITY_MWH_CLAIM_ID,
            allocation_share=ALLOCATION_SHARE_CLAIM_ID,
            allocated_electricity_mwh=ALLOCATED_ELECTRICITY_CLAIM_ID,
        ),
        site_alias=SiteAliasSupport(
            raw_site_id="OCH-01",
            canonical_site_id="ocheong_plant_1",
            binding_id=ALIAS_BINDING_ID,
            obligation_id=ALIAS_OBLIGATION_ID,
            witness_id="w-site-alias-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="site_aliases.OCH-01",
            text="OCH-01 -> ocheong_plant_1",
        ),
        unit_conversion=UnitConversionSupport(
            source_unit="GWh",
            target_unit="MWh",
            factor=GWH_TO_MWH_FACTOR,
            binding_id=UNIT_CONVERSION_BINDING_ID,
            obligation_id=UNIT_CONVERSION_OBLIGATION_ID,
            witness_id="w-unit-conversion-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="unit_conversions.GWh_to_MWh",
            text="1 GWh = 1000 MWh",
        ),
        reporting_period=ReportingPeriodSupport(
            period="2025-03",
            obligation_id=PERIOD_OBLIGATION_ID,
            witness_id="w-reporting-period-policy",
            source="profile:synthetic-raw-claim-acceptance",
            span="reporting_periods.2025-03",
            text="2025-03 is inside the active reporting window",
        ),
        allocation_support=AllocationSupport(
            share=0.5,
            line_a_mass_ton=LINE_A_MASS_TON,
            total_line_mass_ton=TOTAL_LINE_MASS_TON,
            binding_id=ALLOCATION_SUPPORT_BINDING_ID,
            obligation_id=ALLOCATION_SUPPORT_OBLIGATION_ID,
            witness_id="w-allocation-support",
            source="raw_sources/mes_line_mass.csv",
            span="line_mass_row:line_a",
            text="Line A 50,000 ton; total line mass 100,000 ton",
        ),
    )


def _projection_source(report) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


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
