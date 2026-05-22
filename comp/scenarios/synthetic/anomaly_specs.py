from __future__ import annotations

from dataclasses import dataclass

from comp.scenarios.synthetic.anomalies import (
    MISSING_UNIT,
    NEGATIVE_AMOUNT,
    PERIOD_MISMATCH,
    SITE_ALIAS,
    WRONG_UNIT,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    ExpectedFailedClaim,
    ExpectedHazard,
    ExpectedValidationRequirement,
    InjectedAnomaly,
    RawElectricityRow,
    SyntheticResolutionArtifact,
)


@dataclass(frozen=True)
class AnomalySpec:
    row: RawElectricityRow
    anomaly: InjectedAnomaly
    validation_requirement: ExpectedValidationRequirement
    hazard: ExpectedHazard | None
    failed_claim: ExpectedFailedClaim | None


def anomaly_specs(config: SyntheticScenarioConfig) -> tuple[AnomalySpec, ...]:
    specs_by_type = {
        MISSING_UNIT: missing_unit_spec(config),
        WRONG_UNIT: _wrong_unit_spec(config),
        PERIOD_MISMATCH: _period_mismatch_spec(config),
        NEGATIVE_AMOUNT: _negative_amount_spec(config),
        SITE_ALIAS: _site_alias_spec(config),
    }
    return tuple(specs_by_type[anomaly] for anomaly in config.anomalies)


def missing_unit_spec(config: SyntheticScenarioConfig) -> AnomalySpec:
    row_id = "ERP-SYN-PCF-MISSING-UNIT"
    return AnomalySpec(
        row=_anomaly_row(config, row_id=row_id, unit=""),
        anomaly=InjectedAnomaly(
            anomaly_id="synthetic-anomaly:missing_unit",
            anomaly_type=MISSING_UNIT,
            source_row_id=row_id,
            field="unit",
            description="electricity activity row omits its unit",
        ),
        validation_requirement=ExpectedValidationRequirement(
            requirement_id="synthetic-obligation:missing_unit",
            kind="find_source_witness",
            field="unit",
            reason="missing_unit",
        ),
        hazard=ExpectedHazard(
            hazard_id="hazard:missing_unit:unit:review",
            kind="missing_unit",
            field="unit",
            severity="review",
        ),
        failed_claim=None,
    )


def missing_unit_resolution_artifact(
    row: RawElectricityRow,
) -> SyntheticResolutionArtifact:
    return SyntheticResolutionArtifact(
        artifact_id="synthetic-resolution:missing_unit:kwh",
        obligation_id="synthetic-obligation:missing_unit",
        source_row_id=row.source_row_id,
        field="unit",
        resolved_value="kWh",
        witness_id=f"resolution-witness:{row.source_row_id}:unit",
        source_ref="unit_witnesses.csv",
        rationale="operator supplied the omitted electricity unit",
    )


def _wrong_unit_spec(config: SyntheticScenarioConfig) -> AnomalySpec:
    row_id = "ERP-SYN-PCF-WRONG-UNIT"
    return AnomalySpec(
        row=_anomaly_row(config, row_id=row_id, unit="MWh"),
        anomaly=InjectedAnomaly(
            anomaly_id="synthetic-anomaly:wrong_unit",
            anomaly_type=WRONG_UNIT,
            source_row_id=row_id,
            field="unit",
            description="electricity activity row uses an unsupported unit",
        ),
        validation_requirement=ExpectedValidationRequirement(
            requirement_id="synthetic-obligation:wrong_unit",
            kind="find_source_witness",
            field="unit",
            reason="unsupported_unit",
        ),
        hazard=None,
        failed_claim=ExpectedFailedClaim(
            failed_claim_id="synthetic-failed-claim:wrong_unit",
            field="unit",
            value="MWh",
            reason="unsupported_unit",
            source_row_id=row_id,
        ),
    )


def _period_mismatch_spec(config: SyntheticScenarioConfig) -> AnomalySpec:
    row_id = "ERP-SYN-PCF-PERIOD-MISMATCH"
    return AnomalySpec(
        row=_anomaly_row(config, row_id=row_id, period="2023"),
        anomaly=InjectedAnomaly(
            anomaly_id="synthetic-anomaly:period_mismatch",
            anomaly_type=PERIOD_MISMATCH,
            source_row_id=row_id,
            field="period",
            description="electricity activity row falls outside the reporting period",
        ),
        validation_requirement=ExpectedValidationRequirement(
            requirement_id="synthetic-obligation:period_mismatch",
            kind="find_context",
            field="period",
            reason="period_mismatch",
        ),
        hazard=ExpectedHazard(
            hazard_id="hazard:period_mismatch:period:review",
            kind="period_mismatch",
            field="period",
            severity="review",
        ),
        failed_claim=None,
    )


def _negative_amount_spec(config: SyntheticScenarioConfig) -> AnomalySpec:
    row_id = "ERP-SYN-PCF-NEGATIVE-AMOUNT"
    return AnomalySpec(
        row=_anomaly_row(config, row_id=row_id, amount=-25),
        anomaly=InjectedAnomaly(
            anomaly_id="synthetic-anomaly:negative_amount",
            anomaly_type=NEGATIVE_AMOUNT,
            source_row_id=row_id,
            field="electricity_kwh",
            description="electricity activity amount is negative",
        ),
        validation_requirement=ExpectedValidationRequirement(
            requirement_id="synthetic-obligation:negative_amount",
            kind="investigate_activity_amount",
            field="electricity_kwh",
            reason="negative_amount",
        ),
        hazard=ExpectedHazard(
            hazard_id="hazard:invalid_activity_amount:electricity_kwh:block",
            kind="invalid_activity_amount",
            field="electricity_kwh",
            severity="block",
        ),
        failed_claim=ExpectedFailedClaim(
            failed_claim_id="synthetic-failed-claim:negative_amount",
            field="electricity_kwh",
            value=-25,
            reason="negative_amount",
            source_row_id=row_id,
        ),
    )


def _site_alias_spec(config: SyntheticScenarioConfig) -> AnomalySpec:
    row_id = "ERP-SYN-PCF-SITE-ALIAS"
    return AnomalySpec(
        row=_anomaly_row(
            config,
            row_id=row_id,
            site_id="SITE-ALIAS-001",
            site_name="Synthetic Cell Plant One",
        ),
        anomaly=InjectedAnomaly(
            anomaly_id="synthetic-anomaly:site_alias",
            anomaly_type=SITE_ALIAS,
            source_row_id=row_id,
            field="site_id",
            description="electricity activity row uses an unrecognized site alias",
        ),
        validation_requirement=ExpectedValidationRequirement(
            requirement_id="synthetic-obligation:site_alias",
            kind="resolve_site_identity",
            field="site_id",
            reason="site_alias",
        ),
        hazard=ExpectedHazard(
            hazard_id="hazard:site_alias:site_id:review",
            kind="site_alias",
            field="site_id",
            severity="review",
        ),
        failed_claim=None,
    )


def _anomaly_row(
    config: SyntheticScenarioConfig,
    *,
    row_id: str,
    amount: int | float | None = None,
    unit: str | None = None,
    period: str | None = None,
    site_id: str | None = None,
    site_name: str | None = None,
) -> RawElectricityRow:
    return RawElectricityRow(
        source_row_id=row_id,
        source_ref=config.source_ref,
        period=period or config.reporting_period,
        site_id=site_id or config.site_id,
        site_name=site_name or config.site_name,
        product_id=config.product_id,
        activity_type="electricity",
        amount=config.electricity_kwh if amount is None else amount,
        unit=config.electricity_unit if unit is None else unit,
    )


__all__ = [
    "AnomalySpec",
    "anomaly_specs",
    "missing_unit_resolution_artifact",
    "missing_unit_spec",
]
