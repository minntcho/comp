from __future__ import annotations

from decimal import Decimal
from typing import Any

from comp.scenarios.synthetic.anomalies import (
    MISSING_UNIT,
    NEGATIVE_AMOUNT,
    PERIOD_MISMATCH,
    SITE_ALIAS,
    WRONG_UNIT,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest
from comp.scenarios.synthetic.models import (
    ExpectedArtifactRef,
    ExpectedClaim,
    ExpectedDependencyRef,
    ExpectedDerivedClaim,
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
from comp.scenarios.synthetic.sources import (
    _synthetic_source_dependency_refs,
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
                ExpectedDerivedClaim(
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
            expected_receipt=_expected_smoke_receipt(
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
    missing_unit = _missing_unit_spec(config)
    raw_row = missing_unit["row"]
    source_witness_id = f"witness:{raw_row.source_row_id}:electricity_kwh"
    derived_value = _multiply(raw_row.amount, config.factor_value)
    resolution = _missing_unit_resolution_artifact(raw_row)
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
                ExpectedDerivedClaim(
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
                    obligation_id=_reference_search_obligation_id(config),
                    kind="reference_search_required",
                    field="co2e_kg",
                    reason="unknown_reference",
                ),
                ExpectedObligation(
                    obligation_id=_calculation_obligation_id(config),
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
            expected_receipt=_expected_smoke_receipt(
                config,
                source_witness_id=source_witness_id,
                derived_value=derived_value,
                resolved_obligation_ids=(
                    resolved_obligation.obligation_id,
                    _reference_search_obligation_id(config),
                    _calculation_obligation_id(config),
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
    anomaly_specs = _anomaly_specs(config)
    rows = tuple(spec["row"] for spec in anomaly_specs)
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
            expected_obligations=tuple(spec["obligation"] for spec in anomaly_specs),
            expected_hazards=tuple(
                spec["hazard"] for spec in anomaly_specs if spec["hazard"] is not None
            ),
            expected_failed_claims=tuple(
                spec["failed_claim"]
                for spec in anomaly_specs
                if spec["failed_claim"] is not None
            ),
            injected_anomalies=tuple(spec["anomaly"] for spec in anomaly_specs),
            source_to_expected_claim_map=expected_maps,
        ),
    )


def _anomaly_specs(config: SyntheticScenarioConfig) -> tuple[dict[str, Any], ...]:
    specs_by_type = {
        MISSING_UNIT: _missing_unit_spec(config),
        WRONG_UNIT: _wrong_unit_spec(config),
        PERIOD_MISMATCH: _period_mismatch_spec(config),
        NEGATIVE_AMOUNT: _negative_amount_spec(config),
        SITE_ALIAS: _site_alias_spec(config),
    }
    return tuple(specs_by_type[anomaly] for anomaly in config.anomalies)


def _missing_unit_spec(config: SyntheticScenarioConfig) -> dict[str, Any]:
    row_id = "ERP-SYN-PCF-MISSING-UNIT"
    return {
        "row": _anomaly_row(config, row_id=row_id, unit=""),
        "anomaly": InjectedAnomaly(
            anomaly_id="synthetic-anomaly:missing_unit",
            anomaly_type=MISSING_UNIT,
            source_row_id=row_id,
            field="unit",
            description="electricity activity row omits its unit",
        ),
        "obligation": ExpectedObligation(
            obligation_id="synthetic-obligation:missing_unit",
            kind="find_source_witness",
            field="unit",
            reason="missing_unit",
        ),
        "hazard": ExpectedHazard(
            hazard_id="hazard:missing_unit:unit:review",
            kind="missing_unit",
            field="unit",
            severity="review",
        ),
        "failed_claim": None,
    }


def _missing_unit_resolution_artifact(
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


def _wrong_unit_spec(config: SyntheticScenarioConfig) -> dict[str, Any]:
    row_id = "ERP-SYN-PCF-WRONG-UNIT"
    return {
        "row": _anomaly_row(config, row_id=row_id, unit="MWh"),
        "anomaly": InjectedAnomaly(
            anomaly_id="synthetic-anomaly:wrong_unit",
            anomaly_type=WRONG_UNIT,
            source_row_id=row_id,
            field="unit",
            description="electricity activity row uses an unsupported unit",
        ),
        "obligation": ExpectedObligation(
            obligation_id="synthetic-obligation:wrong_unit",
            kind="find_source_witness",
            field="unit",
            reason="unsupported_unit",
        ),
        "hazard": None,
        "failed_claim": ExpectedFailedClaim(
            failed_claim_id="synthetic-failed-claim:wrong_unit",
            field="unit",
            value="MWh",
            reason="unsupported_unit",
            source_row_id=row_id,
        ),
    }


def _period_mismatch_spec(config: SyntheticScenarioConfig) -> dict[str, Any]:
    row_id = "ERP-SYN-PCF-PERIOD-MISMATCH"
    return {
        "row": _anomaly_row(config, row_id=row_id, period="2023"),
        "anomaly": InjectedAnomaly(
            anomaly_id="synthetic-anomaly:period_mismatch",
            anomaly_type=PERIOD_MISMATCH,
            source_row_id=row_id,
            field="period",
            description="electricity activity row falls outside the reporting period",
        ),
        "obligation": ExpectedObligation(
            obligation_id="synthetic-obligation:period_mismatch",
            kind="find_context",
            field="period",
            reason="period_mismatch",
        ),
        "hazard": ExpectedHazard(
            hazard_id="hazard:period_mismatch:period:review",
            kind="period_mismatch",
            field="period",
            severity="review",
        ),
        "failed_claim": None,
    }


def _negative_amount_spec(config: SyntheticScenarioConfig) -> dict[str, Any]:
    row_id = "ERP-SYN-PCF-NEGATIVE-AMOUNT"
    return {
        "row": _anomaly_row(config, row_id=row_id, amount=-25),
        "anomaly": InjectedAnomaly(
            anomaly_id="synthetic-anomaly:negative_amount",
            anomaly_type=NEGATIVE_AMOUNT,
            source_row_id=row_id,
            field="electricity_kwh",
            description="electricity activity amount is negative",
        ),
        "obligation": ExpectedObligation(
            obligation_id="synthetic-obligation:negative_amount",
            kind="investigate_activity_amount",
            field="electricity_kwh",
            reason="negative_amount",
        ),
        "hazard": ExpectedHazard(
            hazard_id="hazard:invalid_activity_amount:electricity_kwh:block",
            kind="invalid_activity_amount",
            field="electricity_kwh",
            severity="block",
        ),
        "failed_claim": ExpectedFailedClaim(
            failed_claim_id="synthetic-failed-claim:negative_amount",
            field="electricity_kwh",
            value=-25,
            reason="negative_amount",
            source_row_id=row_id,
        ),
    }


def _site_alias_spec(config: SyntheticScenarioConfig) -> dict[str, Any]:
    row_id = "ERP-SYN-PCF-SITE-ALIAS"
    return {
        "row": _anomaly_row(
            config,
            row_id=row_id,
            site_id="SITE-ALIAS-001",
            site_name="Synthetic Cell Plant One",
        ),
        "anomaly": InjectedAnomaly(
            anomaly_id="synthetic-anomaly:site_alias",
            anomaly_type=SITE_ALIAS,
            source_row_id=row_id,
            field="site_id",
            description="electricity activity row uses an unrecognized site alias",
        ),
        "obligation": ExpectedObligation(
            obligation_id="synthetic-obligation:site_alias",
            kind="resolve_site_identity",
            field="site_id",
            reason="site_alias",
        ),
        "hazard": ExpectedHazard(
            hazard_id="hazard:site_alias:site_id:review",
            kind="site_alias",
            field="site_id",
            severity="review",
        ),
        "failed_claim": None,
    }


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


def _multiply(left: int | float, right: int | float) -> int | float:
    value = Decimal(str(left)) * Decimal(str(right))
    if value == value.to_integral_value():
        return float(value)
    return float(value)


def _expected_smoke_receipt(
    config: SyntheticScenarioConfig,
    *,
    source_witness_id: str,
    derived_value: int | float,
    resolved_obligation_ids: tuple[str, ...] | None = None,
) -> ExpectedReceipt:
    commit_package_id = f"commit-package:{config.subject_id}"
    governance_decision_id = f"governance-decision:{commit_package_id}"
    manifest_dependency_id = _synthetic_manifest_dependency_id(config)
    resolved_ids = resolved_obligation_ids or (
        _reference_search_obligation_id(config),
        _calculation_obligation_id(config),
    )
    source_dependency_refs = _synthetic_source_dependency_refs(config)
    return ExpectedReceipt(
        public_row_id=config.public_row_id,
        projection_id=config.projection_id,
        authorized_fields=("electricity_kwh", "co2e_kg"),
        public_row={
            "electricity_kwh": config.electricity_kwh,
            "co2e_kg": derived_value,
        },
        governance_status="commit",
        commit_package_id=commit_package_id,
        governance_decision_id=governance_decision_id,
        checked_claim_witness_ids=(source_witness_id,),
        reference_binding_ids=(config.binding_id,),
        derived_claim_ids=(config.output_claim_id,),
        calculation_trace_ids=(f"trace:{config.output_claim_id}",),
        formula_ids=(config.formula_id,),
        resolved_obligation_ids=resolved_ids,
        dependency_refs=(
            ExpectedDependencyRef(
                dependency_kind="synthetic_manifest",
                dependency_id=manifest_dependency_id,
            ),
            *source_dependency_refs,
        ),
        artifact_refs=(
            ExpectedArtifactRef(commit_package_id, "commit_package"),
            ExpectedArtifactRef(governance_decision_id, "governance_decision"),
            ExpectedArtifactRef(
                f"checked_claim:electricity_kwh:{source_witness_id}",
                "checked_claim",
            ),
            ExpectedArtifactRef(config.output_claim_id, "derived_claim"),
            ExpectedArtifactRef(source_witness_id, "evidence_witness"),
            ExpectedArtifactRef(config.binding_id, "reference_binding"),
            ExpectedArtifactRef(
                f"trace:{config.output_claim_id}",
                "calculation_trace",
            ),
            ExpectedArtifactRef(config.formula_id, "formula"),
            ExpectedArtifactRef(manifest_dependency_id, "synthetic_manifest"),
            *(
                ExpectedArtifactRef(
                    ref.dependency_id,
                    ref.dependency_kind,
                )
                for ref in source_dependency_refs
            ),
        ),
    )


def _synthetic_manifest_dependency_id(config: SyntheticScenarioConfig) -> str:
    return f"synthetic_manifest:{config.scenario_id}:seed-{config.seed}"


def _reference_search_obligation_id(config: SyntheticScenarioConfig) -> str:
    return (
        f"resolve:{config.formula_id}:{config.output_claim_id}:"
        "reference_search_required"
    )


def _calculation_obligation_id(config: SyntheticScenarioConfig) -> str:
    return (
        f"calculation:{config.formula_id}:{config.output_claim_id}:"
        "unknown_reference"
    )


__all__ = [
    "ExpectedClaim",
    "ExpectedDerivedClaim",
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
