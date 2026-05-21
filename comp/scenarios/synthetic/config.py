from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from comp.scenarios.synthetic.anomalies import (
    MISSING_UNIT,
    NEGATIVE_AMOUNT,
    PERIOD_MISMATCH,
    SITE_ALIAS,
    WRONG_UNIT,
)


@dataclass(frozen=True)
class SyntheticScenarioConfig:
    scenario_id: str
    seed: int
    profile_id: str
    subject_id: str
    public_row_id: str
    projection_id: str
    reporting_period: str
    site_id: str
    site_name: str
    product_id: str
    electricity_kwh: int | float
    electricity_unit: str
    geography: str
    factor_reference_id: str
    factor_value: int | float
    factor_input_unit: str
    factor_output_unit: str
    source_row_id: str
    source_ref: str
    input_claim_id: str
    output_claim_id: str
    formula_id: str
    selector_rule_id: str
    binding_id: str
    anomalies: tuple[str, ...] = ()

    @classmethod
    def pcf_smoke(cls, *, seed: int = 7) -> "SyntheticScenarioConfig":
        return cls(
            scenario_id="synthetic_pcf.smoke.v1",
            seed=seed,
            profile_id="synthetic-pcf-smoke-profile-v1",
            subject_id="product:synthetic-pcf-smoke-1",
            public_row_id="public-row:synthetic-pcf-smoke-1",
            projection_id="synthetic-pcf-public-row",
            reporting_period="2024",
            site_id="SITE-SYN-001",
            site_name="Synthetic Cell Plant 001",
            product_id="PRD-SYN-001",
            electricity_kwh=1200,
            electricity_unit="kWh",
            geography="KR",
            factor_reference_id="synthetic.factor.kr_grid_2024.location_based",
            factor_value=0.42,
            factor_input_unit="kWh",
            factor_output_unit="kgCO2e",
            source_row_id="ERP-SYN-PCF-0001",
            source_ref="erp_electricity.csv",
            input_claim_id="synthetic-pcf-smoke:electricity:kwh",
            output_claim_id="synthetic-pcf-smoke:electricity:co2e_kg",
            formula_id="pcf.electricity_factor_multiplication.v1",
            selector_rule_id="synthetic.factor_selector.v1",
            binding_id="bind-synthetic-electricity-factor",
        )

    @classmethod
    def pcf_anomaly(cls, *, seed: int = 11) -> "SyntheticScenarioConfig":
        return cls(
            scenario_id="synthetic_pcf.anomaly.v1",
            seed=seed,
            profile_id="synthetic-pcf-anomaly-profile-v1",
            subject_id="product:synthetic-pcf-anomaly-1",
            public_row_id="public-row:synthetic-pcf-anomaly-1",
            projection_id="synthetic-pcf-anomaly-public-row",
            reporting_period="2024",
            site_id="SITE-SYN-001",
            site_name="Synthetic Cell Plant 001",
            product_id="PRD-SYN-001",
            electricity_kwh=1200,
            electricity_unit="kWh",
            geography="KR",
            factor_reference_id="synthetic.factor.kr_grid_2024.location_based",
            factor_value=0.42,
            factor_input_unit="kWh",
            factor_output_unit="kgCO2e",
            source_row_id="ERP-SYN-PCF-ANOMALY",
            source_ref="erp_electricity.csv",
            input_claim_id="synthetic-pcf-anomaly:electricity:kwh",
            output_claim_id="synthetic-pcf-anomaly:electricity:co2e_kg",
            formula_id="pcf.electricity_factor_multiplication.v1",
            selector_rule_id="synthetic.factor_selector.v1",
            binding_id="bind-synthetic-anomaly-electricity-factor",
            anomalies=(
                MISSING_UNIT,
                WRONG_UNIT,
                PERIOD_MISMATCH,
                NEGATIVE_AMOUNT,
                SITE_ALIAS,
            ),
        )

    @classmethod
    def pcf_resolution(cls, *, seed: int = 17) -> "SyntheticScenarioConfig":
        return cls(
            scenario_id="synthetic_pcf.resolution.v1",
            seed=seed,
            profile_id="synthetic-pcf-resolution-profile-v1",
            subject_id="product:synthetic-pcf-resolution-1",
            public_row_id="public-row:synthetic-pcf-resolution-1",
            projection_id="synthetic-pcf-resolution-public-row",
            reporting_period="2024",
            site_id="SITE-SYN-001",
            site_name="Synthetic Cell Plant 001",
            product_id="PRD-SYN-001",
            electricity_kwh=1200,
            electricity_unit="kWh",
            geography="KR",
            factor_reference_id="synthetic.factor.kr_grid_2024.location_based",
            factor_value=0.42,
            factor_input_unit="kWh",
            factor_output_unit="kgCO2e",
            source_row_id="ERP-SYN-PCF-RESOLUTION",
            source_ref="erp_electricity.csv",
            input_claim_id="synthetic-pcf-resolution:electricity:kwh",
            output_claim_id="synthetic-pcf-resolution:electricity:co2e_kg",
            formula_id="pcf.electricity_factor_multiplication.v1",
            selector_rule_id="synthetic.factor_selector.v1",
            binding_id="bind-synthetic-resolution-electricity-factor",
            anomalies=(MISSING_UNIT,),
        )

    def manifest_payload(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "profile_id": self.profile_id,
            "subject_id": self.subject_id,
            "public_row_id": self.public_row_id,
            "projection_id": self.projection_id,
            "reporting_period": self.reporting_period,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "product_id": self.product_id,
            "electricity_kwh": self.electricity_kwh,
            "electricity_unit": self.electricity_unit,
            "geography": self.geography,
            "factor_reference_id": self.factor_reference_id,
            "factor_value": self.factor_value,
            "factor_input_unit": self.factor_input_unit,
            "factor_output_unit": self.factor_output_unit,
            "source_row_id": self.source_row_id,
            "source_ref": self.source_ref,
            "input_claim_id": self.input_claim_id,
            "output_claim_id": self.output_claim_id,
            "formula_id": self.formula_id,
            "selector_rule_id": self.selector_rule_id,
            "binding_id": self.binding_id,
            "anomalies": self.anomalies,
        }


__all__ = ["SyntheticScenarioConfig"]
