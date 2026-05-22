import pytest

from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from comp.compiler_tool import evidence_ref_fingerprint, prepare_commit
from comp.scenarios.synthetic.raw_claim_promotion import (
    AllocationSupport,
    PromotionClaimIds,
    ReportingPeriodSupport,
    SiteAliasSupport,
    SyntheticRawClaimPromotionProfile,
    UnitConversionSupport,
    promote_raw_claim_hypothesis,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_acceptance.scenario import (
    ALIAS_BINDING_ID,
    ALIAS_OBLIGATION_ID,
    ALLOCATED_ELECTRICITY_CLAIM_ID,
    ALLOCATION_SHARE_CLAIM_ID,
    ALLOCATION_SUPPORT_BINDING_ID,
    ALLOCATION_SUPPORT_OBLIGATION_ID,
    ELECTRICITY_MWH_CLAIM_ID,
    FORMULA_ID,
    GWH_TO_MWH_FACTOR,
    LINE_A_MASS_TON,
    PERIOD_OBLIGATION_ID,
    PROFILE_ID,
    PROJECTION_FIELDS,
    PROJECTION_ID,
    PUBLIC_ROW_ID,
    SCENARIO_ID,
    SUBJECT_ID,
    TOTAL_LINE_MASS_TON,
    UNIT_CONVERSION_BINDING_ID,
    UNIT_CONVERSION_OBLIGATION_ID,
)
from tests.domain_scenarios.synthetic_raw_claim_hypothesis_gate.scenario import (
    raw_claim_hypothesis,
)


def test_promotes_supported_raw_candidates_without_projection_authority():
    report = promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )

    assert report.status == "accepted"
    assert report.can_build_public_output is False
    assert ("site_id", "OCH-01") not in {
        (claim.field, claim.value) for claim in report.checked_claims
    }
    assert {
        (claim.field, claim.value, claim.origin)
        for claim in report.checked_claims
    } >= {
        ("site_id", "ocheong_plant_1", "site_alias_binding"),
        ("period", "2025-03", "reporting_period_policy"),
        ("electricity_gwh", 6.4, "raw_candidate_with_unit_policy"),
        ("line_a_mass_ton", 50000, "physical_allocation_support"),
        ("total_line_mass_ton", 100000, "physical_allocation_support"),
    }
    assert tuple(
        (binding.binding_id, binding.reference_id, binding.reference_type)
        for binding in report.canonical_references
    ) == (
        (
            ALIAS_BINDING_ID,
            "site-alias:OCH-01->ocheong_plant_1",
            "site_alias",
        ),
        (
            UNIT_CONVERSION_BINDING_ID,
            "unit-conversion:GWh_to_MWh",
            "unit_conversion",
        ),
        (
            ALLOCATION_SUPPORT_BINDING_ID,
            "physical-allocation-support:line_a_mass_share",
            "physical_allocation_support",
        ),
    )
    assert tuple(item.kind for item in report.resolved_validation_requirements) == (
        "site_alias_resolved",
        "unit_conversion_policy_applied",
        "period_validated",
        "physical_allocation_support_validated",
    )
    assert tuple(claim.claim_id for claim in report.calculated_claims) == (
        ELECTRICITY_MWH_CLAIM_ID,
        ALLOCATION_SHARE_CLAIM_ID,
        ALLOCATED_ELECTRICITY_CLAIM_ID,
    )

    with pytest.raises(PublicOutputBlocked, match="public-output receipt"):
        build_public_output(
            _projection_source(report),
            PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
        )


def test_promoted_report_can_commit_only_through_prepare_commit():
    report = promote_raw_claim_hypothesis(
        raw_claim_hypothesis(),
        _acceptance_profile(),
    )
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

    assert preparation.package.complete is True
    assert preparation.decision.status == "commit"
    assert preparation.receipt is not None
    assert preparation.receipt.citations is not None
    assert preparation.receipt.citations.reference_binding_ids == (
        ALIAS_BINDING_ID,
        UNIT_CONVERSION_BINDING_ID,
        ALLOCATION_SUPPORT_BINDING_ID,
    )
    assert preparation.receipt.citations.derived_claim_ids == (
        ELECTRICITY_MWH_CLAIM_ID,
        ALLOCATION_SHARE_CLAIM_ID,
        ALLOCATED_ELECTRICITY_CLAIM_ID,
    )

    projection = build_public_output(
        _projection_source(report),
        PublicOutputSpec(PROJECTION_ID, PROJECTION_FIELDS),
        receipt=preparation.receipt,
    )
    assert projection == {
        "site_id": "ocheong_plant_1",
        "period": "2025-03",
        "electricity_mwh": 6400,
        "allocation_share": 0.5,
        "allocated_electricity_mwh": 3200,
    }


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


def _projection_source(report):
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values
