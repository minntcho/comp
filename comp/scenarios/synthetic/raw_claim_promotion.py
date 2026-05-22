from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    ValidationReport,
    CalculatedClaim,
    EvidenceRef,
    ValidationRequirement,
    CanonicalReference,
    with_recomputed_status,
)
from comp.compiler_tool.models import InterpretationHypothesis


@dataclass(frozen=True)
class PromotionClaimIds:
    electricity_mwh: str
    allocation_share: str
    allocated_electricity_mwh: str


@dataclass(frozen=True)
class SiteAliasSupport:
    raw_site_id: str
    canonical_site_id: str
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class UnitConversionSupport:
    source_unit: str
    target_unit: str
    factor: Decimal | int | float | str
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class ReportingPeriodSupport:
    period: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class AllocationSupport:
    share: Decimal | int | float | str
    line_a_mass_ton: int | float
    total_line_mass_ton: int | float
    binding_id: str
    obligation_id: str
    witness_id: str
    source: str
    span: str
    text: str


@dataclass(frozen=True)
class SyntheticRawClaimPromotionProfile:
    profile_id: str
    scenario_id: str
    formula_id: str
    selector_rule_id: str
    claim_ids: PromotionClaimIds
    site_alias: SiteAliasSupport
    unit_conversion: UnitConversionSupport
    reporting_period: ReportingPeriodSupport
    allocation_support: AllocationSupport


def promote_raw_claim_hypothesis(
    hypothesis: InterpretationHypothesis,
    profile: SyntheticRawClaimPromotionProfile,
) -> ValidationReport:
    raw = _raw_claim_values(hypothesis)
    electricity = _electricity_claim(raw)
    electricity_gwh = _decimal(electricity["amount"])
    electricity_mwh = electricity_gwh * _decimal(profile.unit_conversion.factor)
    allocation_share = _decimal(profile.allocation_support.share)
    allocated_electricity_mwh = electricity_mwh * allocation_share

    return with_recomputed_status(
        ValidationReport(
            status="accepted",
            evidence_refs=(
                *hypothesis.witnesses,
                *_support_witnesses(profile),
            ),
            checked_claims=(
                CheckedClaim(
                    field="site_id",
                    value=profile.site_alias.canonical_site_id,
                    witness_id=profile.site_alias.witness_id,
                    origin="site_alias_binding",
                ),
                CheckedClaim(
                    field="period",
                    value=profile.reporting_period.period,
                    witness_id=profile.reporting_period.witness_id,
                    origin="reporting_period_policy",
                ),
                CheckedClaim(
                    field="electricity_gwh",
                    value=_number(electricity_gwh),
                    witness_id=str(raw["electricity_witness_id"]),
                    origin="raw_candidate_with_unit_policy",
                ),
                CheckedClaim(
                    field="line_a_mass_ton",
                    value=profile.allocation_support.line_a_mass_ton,
                    witness_id=profile.allocation_support.witness_id,
                    origin="physical_allocation_support",
                ),
                CheckedClaim(
                    field="total_line_mass_ton",
                    value=profile.allocation_support.total_line_mass_ton,
                    witness_id=profile.allocation_support.witness_id,
                    origin="physical_allocation_support",
                ),
            ),
            resolved_validation_requirements=_resolved_validation_requirements(profile),
            canonical_references=_canonical_references(profile),
            calculated_claims=_calculated_claims(
                profile,
                electricity_mwh=electricity_mwh,
                allocation_share=allocation_share,
                allocated_electricity_mwh=allocated_electricity_mwh,
            ),
            can_build_public_output=False,
        )
    )


def _raw_claim_values(hypothesis: InterpretationHypothesis) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for claim in hypothesis.claims:
        values[claim.field] = claim.value
        if claim.witness_id is not None:
            values[f"{claim.field}_witness_id"] = claim.witness_id
    return values


def _electricity_claim(values: dict[str, Any]) -> dict[str, Any]:
    electricity = values["electricity"]
    if not isinstance(electricity, dict):
        raise TypeError("raw electricity claim must be a mapping.")
    return electricity


def _support_witnesses(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[EvidenceRef, ...]:
    return (
        EvidenceRef(
            witness_id=profile.site_alias.witness_id,
            field="site_alias",
            source=profile.site_alias.source,
            span=profile.site_alias.span,
            text=profile.site_alias.text,
        ),
        EvidenceRef(
            witness_id=profile.unit_conversion.witness_id,
            field="unit_conversion",
            source=profile.unit_conversion.source,
            span=profile.unit_conversion.span,
            text=profile.unit_conversion.text,
        ),
        EvidenceRef(
            witness_id=profile.reporting_period.witness_id,
            field="period",
            source=profile.reporting_period.source,
            span=profile.reporting_period.span,
            text=profile.reporting_period.text,
        ),
        EvidenceRef(
            witness_id=profile.allocation_support.witness_id,
            field="allocation_support",
            source=profile.allocation_support.source,
            span=profile.allocation_support.span,
            text=profile.allocation_support.text,
        ),
    )


def _resolved_validation_requirements(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[ValidationRequirement, ...]:
    return (
        ValidationRequirement(
            kind="site_alias_resolved",
            field="site_id",
            reason=(
                f"{profile.site_alias.raw_site_id}_alias_bound_to_"
                f"{profile.site_alias.canonical_site_id}"
            ),
            obligation_id=profile.site_alias.obligation_id,
        ),
        ValidationRequirement(
            kind="unit_conversion_policy_applied",
            field="electricity_mwh",
            reason=(
                f"{profile.unit_conversion.source_unit}_to_"
                f"{profile.unit_conversion.target_unit}_conversion_factor_"
                f"{_number(_decimal(profile.unit_conversion.factor))}"
            ),
            obligation_id=profile.unit_conversion.obligation_id,
        ),
        ValidationRequirement(
            kind="period_validated",
            field="period",
            reason="period_inside_active_reporting_window",
            obligation_id=profile.reporting_period.obligation_id,
        ),
        ValidationRequirement(
            kind="physical_allocation_support_validated",
            field="allocation_share",
            reason="line_a_mass_over_total_line_mass",
            obligation_id=profile.allocation_support.obligation_id,
        ),
    )


def _canonical_references(
    profile: SyntheticRawClaimPromotionProfile,
) -> tuple[CanonicalReference, ...]:
    return (
        CanonicalReference(
            binding_id=profile.site_alias.binding_id,
            claim_id=profile.scenario_id,
            reference_id=(
                f"site-alias:{profile.site_alias.raw_site_id}->"
                f"{profile.site_alias.canonical_site_id}"
            ),
            reference_type="site_alias",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.site_alias.witness_id,),
        ),
        CanonicalReference(
            binding_id=profile.unit_conversion.binding_id,
            claim_id=profile.scenario_id,
            reference_id=(
                f"unit-conversion:{profile.unit_conversion.source_unit}_to_"
                f"{profile.unit_conversion.target_unit}"
            ),
            reference_type="unit_conversion",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.unit_conversion.witness_id,),
        ),
        CanonicalReference(
            binding_id=profile.allocation_support.binding_id,
            claim_id=profile.scenario_id,
            reference_id="physical-allocation-support:line_a_mass_share",
            reference_type="physical_allocation_support",
            selector_rule_id=profile.selector_rule_id,
            source_witness_ids=(profile.allocation_support.witness_id,),
        ),
    )


def _calculated_claims(
    profile: SyntheticRawClaimPromotionProfile,
    *,
    electricity_mwh: Decimal,
    allocation_share: Decimal,
    allocated_electricity_mwh: Decimal,
) -> tuple[CalculatedClaim, ...]:
    return (
        _derived_claim(
            claim_id=profile.claim_ids.electricity_mwh,
            field="electricity_mwh",
            value=_number(electricity_mwh),
            unit=profile.unit_conversion.target_unit,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=("electricity_gwh",),
            reference_binding_ids=(profile.unit_conversion.binding_id,),
            steps=(
                CalculationStep(
                    step_id="convert-gwh-to-mwh",
                    operation="multiply",
                    input_ids=("electricity_gwh", profile.unit_conversion.binding_id),
                    output_value=_number(electricity_mwh),
                    output_unit=profile.unit_conversion.target_unit,
                ),
            ),
        ),
        _derived_claim(
            claim_id=profile.claim_ids.allocation_share,
            field="allocation_share",
            value=_number(allocation_share),
            unit=None,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=("line_a_mass_ton", "total_line_mass_ton"),
            reference_binding_ids=(profile.allocation_support.binding_id,),
            steps=(
                CalculationStep(
                    step_id="line-a-allocation-share",
                    operation="divide",
                    input_ids=("line_a_mass_ton", "total_line_mass_ton"),
                    output_value=_number(allocation_share),
                ),
            ),
        ),
        _derived_claim(
            claim_id=profile.claim_ids.allocated_electricity_mwh,
            field="allocated_electricity_mwh",
            value=_number(allocated_electricity_mwh),
            unit=profile.unit_conversion.target_unit,
            formula_id=profile.formula_id,
            origin="raw_claim_hypothesis_acceptance_calculated",
            input_claim_ids=(
                profile.claim_ids.electricity_mwh,
                profile.claim_ids.allocation_share,
            ),
            reference_binding_ids=(
                profile.unit_conversion.binding_id,
                profile.allocation_support.binding_id,
            ),
            steps=(
                CalculationStep(
                    step_id="allocated-electricity-mwh",
                    operation="multiply",
                    input_ids=(
                        profile.claim_ids.electricity_mwh,
                        profile.claim_ids.allocation_share,
                    ),
                    output_value=_number(allocated_electricity_mwh),
                    output_unit=profile.unit_conversion.target_unit,
                ),
            ),
        ),
    )


def _derived_claim(
    *,
    claim_id: str,
    field: str,
    value: int | float,
    unit: str | None,
    formula_id: str,
    origin: str,
    input_claim_ids: tuple[str, ...],
    reference_binding_ids: tuple[str, ...],
    steps: tuple[CalculationStep, ...],
) -> CalculatedClaim:
    return CalculatedClaim(
        claim_id=claim_id,
        field=field,
        value=value,
        unit=unit,
        origin=origin,
        trace=CalculationTrace(
            trace_id=f"trace:{claim_id}",
            formula_id=formula_id,
            input_claim_ids=input_claim_ids,
            reference_binding_ids=reference_binding_ids,
            steps=steps,
        ),
    )


def _decimal(value: Decimal | int | float | str | Any) -> Decimal:
    return Decimal(str(value))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


__all__ = [
    "AllocationSupport",
    "PromotionClaimIds",
    "ReportingPeriodSupport",
    "SiteAliasSupport",
    "SyntheticRawClaimPromotionProfile",
    "UnitConversionSupport",
    "promote_raw_claim_hypothesis",
]
