from __future__ import annotations

from decimal import Decimal

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    ExpectedCalculatedClaim,
    ExpectedClaim,
    ExpectedSourceMap,
    MasterReferenceRecord,
    RawElectricityRow,
    SyntheticMaster,
)


def pcf_reference_record(config: SyntheticScenarioConfig) -> MasterReferenceRecord:
    return MasterReferenceRecord(
        reference_id=config.factor_reference_id,
        reference_type="emission_factor",
        label=f"{config.geography} grid electricity factor {config.reporting_period}",
        geography=config.geography,
        valid_period=config.reporting_period,
        method="location_based",
        factor_value=config.factor_value,
        input_unit=config.factor_input_unit,
        output_unit=config.factor_output_unit,
        source="synthetic_reference_catalog",
        witness_id=f"reference-witness:{config.factor_reference_id}",
    )


def pcf_master(config: SyntheticScenarioConfig) -> SyntheticMaster:
    return SyntheticMaster(
        reference_catalog=(pcf_reference_record(config),),
        sites=(
            {
                "site_id": config.site_id,
                "site_name": config.site_name,
                "geography": config.geography,
            },
        ),
        products=(
            {
                "product_id": config.product_id,
                "site_id": config.site_id,
            },
        ),
    )


def raw_electricity_row(config: SyntheticScenarioConfig) -> RawElectricityRow:
    return RawElectricityRow(
        source_row_id=config.source_row_id,
        source_ref=config.source_ref,
        period=config.reporting_period,
        site_id=config.site_id,
        site_name=config.site_name,
        product_id=config.product_id,
        activity_type="electricity",
        amount=config.electricity_kwh,
        unit=config.electricity_unit,
    )


def electricity_witness_id(source_row_id: str) -> str:
    return f"witness:{source_row_id}:electricity_kwh"


def calculate_co2e_value(
    activity_amount: int | float,
    factor_value: int | float,
) -> int | float:
    value = Decimal(str(activity_amount)) * Decimal(str(factor_value))
    if value == value.to_integral_value():
        return float(value)
    return float(value)


def electricity_expected_claim(
    claim_id: str,
    row: RawElectricityRow,
    *,
    unit: str | None = None,
) -> ExpectedClaim:
    claim_unit = row.unit or None if unit is None else unit
    return ExpectedClaim(
        claim_id=claim_id,
        field="electricity_kwh",
        value=row.amount,
        unit=claim_unit,
        witness_id=electricity_witness_id(row.source_row_id),
        source_row_id=row.source_row_id,
    )


def electricity_source_map(
    expected_claim_id: str,
    row: RawElectricityRow,
) -> ExpectedSourceMap:
    return ExpectedSourceMap(
        source_ref=row.source_ref,
        source_row_id=row.source_row_id,
        expected_claim_id=expected_claim_id,
        expected_field="electricity_kwh",
        witness_id=electricity_witness_id(row.source_row_id),
    )


def co2e_expected_calculated_claim(
    config: SyntheticScenarioConfig,
    value: int | float,
) -> ExpectedCalculatedClaim:
    return ExpectedCalculatedClaim(
        claim_id=config.output_claim_id,
        field="co2e_kg",
        value=value,
        unit=config.factor_output_unit,
        formula_id=config.formula_id,
    )


__all__ = [
    "calculate_co2e_value",
    "co2e_expected_calculated_claim",
    "electricity_expected_claim",
    "electricity_source_map",
    "electricity_witness_id",
    "pcf_master",
    "pcf_reference_record",
    "raw_electricity_row",
]
