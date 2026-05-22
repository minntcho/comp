from __future__ import annotations

from decimal import Decimal

from comp.scenarios.synthetic.anomaly_specs import (
    anomaly_specs,
    missing_unit_resolution_artifact,
    missing_unit_spec,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest
from comp.scenarios.synthetic.models import (
    ExpectedArtifactRef,
    ExpectedClaim,
    ExpectedDependencyRef,
    ExpectedCalculatedClaim,
    ExpectedFailedClaim,
    ExpectedHazard,
    ExpectedObligation,
    ExpectedReceipt,
    ExpectedResolutionArtifact,
    ExpectedSourceMap,
    InjectedAnomaly,
    MasterReferenceRecord,
    OUTPUT_CONTRACT,
    RESOLUTION_OUTPUT_CONTRACT,
    SYNTHETIC_SOURCE_INPUT_KIND,
    RawElectricityRow,
    SyntheticInputBundle,
    SyntheticLoadedSource,
    SyntheticMaster,
    SyntheticOracle,
    SyntheticRawSources,
    SyntheticResolutionArtifact,
    SyntheticResolutionArtifacts,
    SyntheticRun,
)
from comp.scenarios.synthetic.oracle import (
    calculation_obligation_id,
    expected_smoke_receipt,
    reference_search_obligation_id,
)
from comp.scenarios.synthetic.sources import (
    build_synthetic_loaded_source,
    build_synthetic_loaded_sources,
    synthetic_source_input_dependency_id,
)


def generate_synthetic_pcf_run(config: SyntheticScenarioConfig) -> SyntheticRun:
    if config.scenario_id == "synthetic_pcf.resolution.v1":
        return _generate_synthetic_pcf_resolution_run(config)
    if config.anomalies:
        return _generate_synthetic_pcf_anomaly_run(config)

    source_witness_id = f"witness:{config.source_row_id}:electricity_kwh"
    derived_value = _multiply(config.electricity_kwh, config.factor_value)
    reference = MasterReferenceRecord(
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
    raw_row = RawElectricityRow(
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
    expected_claim = ExpectedClaim(
        claim_id=config.input_claim_id,
        field="electricity_kwh",
        value=config.electricity_kwh,
        unit=config.electricity_unit,
        witness_id=source_witness_id,
        source_row_id=config.source_row_id,
    )
    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=SyntheticMaster(
            reference_catalog=(reference,),
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
        ),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        oracle=SyntheticOracle(
            expected_claims=(expected_claim,),
            expected_derived_claims=(
                ExpectedCalculatedClaim(
                    claim_id=config.output_claim_id,
                    field="co2e_kg",
                    value=derived_value,
                    unit=config.factor_output_unit,
                    formula_id=config.formula_id,
                ),
            ),
            expected_obligations=(),
            expected_hazards=(),
            expected_failed_claims=(),
            injected_anomalies=(),
            source_to_expected_claim_map=(
                ExpectedSourceMap(
                    source_ref=config.source_ref,
                    source_row_id=config.source_row_id,
                    expected_claim_id=config.input_claim_id,
                    expected_field="electricity_kwh",
                    witness_id=source_witness_id,
                ),
            ),
            expected_receipt=expected_smoke_receipt(
                config,
                source_witness_id=source_witness_id,
                derived_value=derived_value,
            ),
        ),
    )


def _generate_synthetic_pcf_resolution_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    reference = MasterReferenceRecord(
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
    missing_unit = missing_unit_spec(config)
    raw_row = missing_unit["row"]
    source_witness_id = f"witness:{raw_row.source_row_id}:electricity_kwh"
    derived_value = _multiply(raw_row.amount, config.factor_value)
    resolution = missing_unit_resolution_artifact(raw_row)
    resolved_obligation = missing_unit["obligation"]

    return SyntheticRun(
        config=config,
        manifest=build_manifest(
            config,
            output_contract=RESOLUTION_OUTPUT_CONTRACT,
        ),
        master=SyntheticMaster(
            reference_catalog=(reference,),
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
        ),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        resolution_artifacts=SyntheticResolutionArtifacts(
            unit_witnesses=(resolution,),
        ),
        oracle=SyntheticOracle(
            expected_claims=(
                ExpectedClaim(
                    claim_id=config.input_claim_id,
                    field="electricity_kwh",
                    value=raw_row.amount,
                    unit=resolution.resolved_value,
                    witness_id=source_witness_id,
                    source_row_id=raw_row.source_row_id,
                ),
            ),
            expected_derived_claims=(
                ExpectedCalculatedClaim(
                    claim_id=config.output_claim_id,
                    field="co2e_kg",
                    value=derived_value,
                    unit=config.factor_output_unit,
                    formula_id=config.formula_id,
                ),
            ),
            expected_obligations=(),
            expected_hazards=(),
            expected_failed_claims=(),
            injected_anomalies=(missing_unit["anomaly"],),
            source_to_expected_claim_map=(
                ExpectedSourceMap(
                    source_ref=raw_row.source_ref,
                    source_row_id=raw_row.source_row_id,
                    expected_claim_id=config.input_claim_id,
                    expected_field="electricity_kwh",
                    witness_id=source_witness_id,
                ),
            ),
            expected_resolved_obligations=(
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


def _generate_synthetic_pcf_anomaly_run(
    config: SyntheticScenarioConfig,
) -> SyntheticRun:
    reference = MasterReferenceRecord(
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
    specs = anomaly_specs(config)
    rows = tuple(spec["row"] for spec in specs)
    expected_claims = tuple(
        ExpectedClaim(
            claim_id=f"synthetic-pcf-anomaly:{row.source_row_id}:electricity_kwh",
            field="electricity_kwh",
            value=row.amount,
            unit=row.unit or None,
            witness_id=f"witness:{row.source_row_id}:electricity_kwh",
            source_row_id=row.source_row_id,
        )
        for row in rows
        if float(row.amount) >= 0
    )
    expected_maps = tuple(
        ExpectedSourceMap(
            source_ref=row.source_ref,
            source_row_id=row.source_row_id,
            expected_claim_id=f"synthetic-pcf-anomaly:{row.source_row_id}:electricity_kwh",
            expected_field="electricity_kwh",
            witness_id=f"witness:{row.source_row_id}:electricity_kwh",
        )
        for row in rows
        if float(row.amount) >= 0
    )

    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=SyntheticMaster(
            reference_catalog=(reference,),
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
        ),
        raw_sources=SyntheticRawSources(electricity_rows=rows),
        oracle=SyntheticOracle(
            expected_claims=expected_claims,
            expected_derived_claims=(),
            expected_obligations=tuple(spec["obligation"] for spec in specs),
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


def _multiply(left: int | float, right: int | float) -> int | float:
    value = Decimal(str(left)) * Decimal(str(right))
    if value == value.to_integral_value():
        return float(value)
    return float(value)


__all__ = [
    "ExpectedClaim",
    "ExpectedCalculatedClaim",
    "ExpectedFailedClaim",
    "ExpectedHazard",
    "ExpectedObligation",
    "ExpectedArtifactRef",
    "ExpectedDependencyRef",
    "ExpectedReceipt",
    "ExpectedResolutionArtifact",
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "OUTPUT_CONTRACT",
    "RawElectricityRow",
    "RESOLUTION_OUTPUT_CONTRACT",
    "SYNTHETIC_SOURCE_INPUT_KIND",
    "SyntheticLoadedSource",
    "SyntheticInputBundle",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticRawSources",
    "SyntheticResolutionArtifact",
    "SyntheticResolutionArtifacts",
    "SyntheticRun",
    "build_synthetic_loaded_source",
    "build_synthetic_loaded_sources",
    "generate_synthetic_pcf_run",
    "synthetic_source_input_dependency_id",
]
