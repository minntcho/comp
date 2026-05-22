from __future__ import annotations

from comp.scenarios.synthetic.anomaly_specs import (
    anomaly_specs,
    missing_unit_resolution_artifact,
    missing_unit_spec,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest
from comp.scenarios.synthetic.models import (
    ExpectedObligation,
    ExpectedResolutionArtifact,
    OUTPUT_CONTRACT,
    RESOLUTION_OUTPUT_CONTRACT,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticResolutionArtifacts,
    SyntheticRun,
)
from comp.scenarios.synthetic.oracle import (
    calculation_obligation_id,
    expected_smoke_receipt,
    reference_search_obligation_id,
)
from comp.scenarios.synthetic.pcf_fixtures import (
    calculate_co2e_value,
    co2e_expected_calculated_claim,
    electricity_expected_claim,
    electricity_source_map,
    electricity_witness_id,
    pcf_master,
    raw_electricity_row,
)


def build_synthetic_pcf_smoke_run(config: SyntheticScenarioConfig) -> SyntheticRun:
    raw_row = raw_electricity_row(config)
    source_witness_id = electricity_witness_id(raw_row.source_row_id)
    derived_value = calculate_co2e_value(raw_row.amount, config.factor_value)
    expected_claim = electricity_expected_claim(config.input_claim_id, raw_row)
    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        oracle=SyntheticOracle(
            expected_claims=(expected_claim,),
            expected_calculated_claims=(
                co2e_expected_calculated_claim(config, derived_value),
            ),
            expected_validation_requirements=(),
            expected_hazards=(),
            expected_failed_claims=(),
            injected_anomalies=(),
            source_to_expected_claim_map=(
                electricity_source_map(config.input_claim_id, raw_row),
            ),
            expected_receipt=expected_smoke_receipt(
                config,
                source_witness_id=source_witness_id,
                derived_value=derived_value,
            ),
        ),
    )


def build_synthetic_pcf_resolution_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    missing_unit = missing_unit_spec(config)
    raw_row = missing_unit["row"]
    source_witness_id = electricity_witness_id(raw_row.source_row_id)
    derived_value = calculate_co2e_value(raw_row.amount, config.factor_value)
    resolution = missing_unit_resolution_artifact(raw_row)
    resolved_obligation = missing_unit["obligation"]

    return SyntheticRun(
        config=config,
        manifest=build_manifest(
            config,
            output_contract=RESOLUTION_OUTPUT_CONTRACT,
        ),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        resolution_artifacts=SyntheticResolutionArtifacts(
            unit_witnesses=(resolution,),
        ),
        oracle=SyntheticOracle(
            expected_claims=(
                electricity_expected_claim(
                    config.input_claim_id,
                    raw_row,
                    unit=resolution.resolved_value,
                ),
            ),
            expected_calculated_claims=(
                co2e_expected_calculated_claim(config, derived_value),
            ),
            expected_validation_requirements=(),
            expected_hazards=(),
            expected_failed_claims=(),
            injected_anomalies=(missing_unit["anomaly"],),
            source_to_expected_claim_map=(
                electricity_source_map(config.input_claim_id, raw_row),
            ),
            expected_resolved_validation_requirements=(
                resolved_obligation,
                ExpectedObligation(
                    obligation_id=reference_search_obligation_id(config),
                    kind="reference_search_required",
                    field="co2e_kg",
                    reason="unknown_reference",
                ),
                ExpectedObligation(
                    obligation_id=calculation_obligation_id(config),
                    kind="calculation_blocked",
                    field="co2e_kg",
                    reason="unknown_reference",
                ),
            ),
            expected_resolution_artifacts=(
                ExpectedResolutionArtifact(
                    artifact_id=resolution.artifact_id,
                    obligation_id=resolution.obligation_id,
                    source_row_id=resolution.source_row_id,
                    field=resolution.field,
                    resolved_value=resolution.resolved_value,
                    witness_id=resolution.witness_id,
                    source_ref=resolution.source_ref,
                ),
            ),
            expected_receipt=expected_smoke_receipt(
                config,
                source_witness_id=source_witness_id,
                derived_value=derived_value,
                resolved_obligation_ids=(
                    resolved_obligation.obligation_id,
                    reference_search_obligation_id(config),
                    calculation_obligation_id(config),
                ),
            ),
        ),
        output_contract=RESOLUTION_OUTPUT_CONTRACT,
    )


def build_synthetic_pcf_anomaly_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    specs = anomaly_specs(config)
    rows = tuple(spec["row"] for spec in specs)
    expected_claims = tuple(
        electricity_expected_claim(
            f"synthetic-pcf-anomaly:{row.source_row_id}:electricity_kwh",
            row,
        )
        for row in rows
        if float(row.amount) >= 0
    )
    expected_maps = tuple(
        electricity_source_map(
            f"synthetic-pcf-anomaly:{row.source_row_id}:electricity_kwh",
            row,
        )
        for row in rows
        if float(row.amount) >= 0
    )

    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=pcf_master(config),
        raw_sources=SyntheticRawSources(electricity_rows=rows),
        oracle=SyntheticOracle(
            expected_claims=expected_claims,
            expected_calculated_claims=(),
            expected_validation_requirements=tuple(spec["obligation"] for spec in specs),
            expected_hazards=tuple(
                spec["hazard"] for spec in specs if spec["hazard"] is not None
            ),
            expected_failed_claims=tuple(
                spec["failed_claim"]
                for spec in specs
                if spec["failed_claim"] is not None
            ),
            injected_anomalies=tuple(spec["anomaly"] for spec in specs),
            source_to_expected_claim_map=expected_maps,
        ),
    )

__all__ = [
    "build_synthetic_pcf_anomaly_run",
    "build_synthetic_pcf_resolution_run",
    "build_synthetic_pcf_smoke_run",
]
