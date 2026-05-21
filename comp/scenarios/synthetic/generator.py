from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from comp.scenarios.synthetic.anomalies import (
    MISSING_UNIT,
    NEGATIVE_AMOUNT,
    PERIOD_MISMATCH,
    SITE_ALIAS,
    WRONG_UNIT,
)
from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest


OUTPUT_CONTRACT = ("master", "raw_sources", "oracle")
SYNTHETIC_SOURCE_INPUT_KIND = "synthetic_source_input"


@dataclass(frozen=True)
class MasterReferenceRecord:
    reference_id: str
    reference_type: str
    label: str
    geography: str
    valid_period: str
    method: str
    factor_value: int | float
    input_unit: str
    output_unit: str
    source: str
    witness_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "label": self.label,
            "geography": self.geography,
            "valid_period": self.valid_period,
            "method": self.method,
            "factor_value": self.factor_value,
            "input_unit": self.input_unit,
            "output_unit": self.output_unit,
            "source": self.source,
            "witness_id": self.witness_id,
        }


@dataclass(frozen=True)
class RawElectricityRow:
    source_row_id: str
    source_ref: str
    period: str
    site_id: str
    site_name: str
    product_id: str
    activity_type: str
    amount: int | float
    unit: str

    def to_row(self) -> dict[str, Any]:
        return {
            "source_row_id": self.source_row_id,
            "source_ref": self.source_ref,
            "period": self.period,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "product_id": self.product_id,
            "activity_type": self.activity_type,
            "amount": self.amount,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class ExpectedClaim:
    claim_id: str
    field: str
    value: int | float | str
    unit: str | None
    witness_id: str
    source_row_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "field": self.field,
            "value": self.value,
            "unit": self.unit or "",
            "witness_id": self.witness_id,
            "source_row_id": self.source_row_id,
        }


@dataclass(frozen=True)
class ExpectedDerivedClaim:
    claim_id: str
    field: str
    value: int | float
    unit: str
    formula_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "field": self.field,
            "value": self.value,
            "unit": self.unit,
            "formula_id": self.formula_id,
        }


@dataclass(frozen=True)
class ExpectedSourceMap:
    source_ref: str
    source_row_id: str
    expected_claim_id: str
    expected_field: str
    witness_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "source_row_id": self.source_row_id,
            "expected_claim_id": self.expected_claim_id,
            "expected_field": self.expected_field,
            "witness_id": self.witness_id,
        }


@dataclass(frozen=True)
class InjectedAnomaly:
    anomaly_id: str
    anomaly_type: str
    source_row_id: str
    field: str
    description: str

    def to_row(self) -> dict[str, Any]:
        return {
            "anomaly_id": self.anomaly_id,
            "anomaly_type": self.anomaly_type,
            "source_row_id": self.source_row_id,
            "field": self.field,
            "description": self.description,
        }


@dataclass(frozen=True)
class ExpectedFailedClaim:
    failed_claim_id: str
    field: str
    value: int | float | str
    reason: str
    source_row_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "failed_claim_id": self.failed_claim_id,
            "field": self.field,
            "value": self.value,
            "reason": self.reason,
            "source_row_id": self.source_row_id,
        }


@dataclass(frozen=True)
class ExpectedObligation:
    obligation_id: str
    kind: str
    field: str
    reason: str

    def to_row(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "kind": self.kind,
            "field": self.field,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ExpectedHazard:
    hazard_id: str
    kind: str
    field: str
    severity: str

    def to_row(self) -> dict[str, Any]:
        return {
            "hazard_id": self.hazard_id,
            "kind": self.kind,
            "field": self.field,
            "severity": self.severity,
        }


@dataclass(frozen=True)
class ExpectedArtifactRef:
    artifact_id: str
    artifact_kind: str

    def to_payload(self) -> dict[str, str]:
        return {
            "artifact_id": self.artifact_id,
            "artifact_kind": self.artifact_kind,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ExpectedArtifactRef":
        return cls(
            artifact_id=str(payload["artifact_id"]),
            artifact_kind=str(payload["artifact_kind"]),
        )


@dataclass(frozen=True)
class ExpectedDependencyRef:
    dependency_kind: str
    dependency_id: str

    def to_payload(self) -> dict[str, str]:
        return {
            "dependency_kind": self.dependency_kind,
            "dependency_id": self.dependency_id,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ExpectedDependencyRef":
        return cls(
            dependency_kind=str(payload["dependency_kind"]),
            dependency_id=str(payload["dependency_id"]),
        )


@dataclass(frozen=True)
class ExpectedReceipt:
    public_row_id: str
    projection_id: str
    authorized_fields: tuple[str, ...]
    public_row: dict[str, Any]
    governance_status: str
    commit_package_id: str
    governance_decision_id: str
    checked_claim_witness_ids: tuple[str, ...]
    reference_binding_ids: tuple[str, ...]
    derived_claim_ids: tuple[str, ...]
    calculation_trace_ids: tuple[str, ...]
    formula_ids: tuple[str, ...]
    dependency_refs: tuple[ExpectedDependencyRef, ...]
    artifact_refs: tuple[ExpectedArtifactRef, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "public_row_id": self.public_row_id,
            "projection_id": self.projection_id,
            "authorized_fields": list(self.authorized_fields),
            "public_row": self.public_row,
            "governance_status": self.governance_status,
            "commit_package_id": self.commit_package_id,
            "governance_decision_id": self.governance_decision_id,
            "checked_claim_witness_ids": list(self.checked_claim_witness_ids),
            "reference_binding_ids": list(self.reference_binding_ids),
            "derived_claim_ids": list(self.derived_claim_ids),
            "calculation_trace_ids": list(self.calculation_trace_ids),
            "formula_ids": list(self.formula_ids),
            "dependency_refs": [
                ref.to_payload() for ref in self.dependency_refs
            ],
            "artifact_refs": [ref.to_payload() for ref in self.artifact_refs],
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ExpectedReceipt":
        return cls(
            public_row_id=str(payload["public_row_id"]),
            projection_id=str(payload["projection_id"]),
            authorized_fields=tuple(payload["authorized_fields"]),
            public_row=dict(payload["public_row"]),
            governance_status=str(payload["governance_status"]),
            commit_package_id=str(payload["commit_package_id"]),
            governance_decision_id=str(payload["governance_decision_id"]),
            checked_claim_witness_ids=tuple(payload["checked_claim_witness_ids"]),
            reference_binding_ids=tuple(payload["reference_binding_ids"]),
            derived_claim_ids=tuple(payload["derived_claim_ids"]),
            calculation_trace_ids=tuple(payload["calculation_trace_ids"]),
            formula_ids=tuple(payload["formula_ids"]),
            dependency_refs=tuple(
                ExpectedDependencyRef.from_payload(ref)
                for ref in payload["dependency_refs"]
            ),
            artifact_refs=tuple(
                ExpectedArtifactRef.from_payload(ref)
                for ref in payload["artifact_refs"]
            ),
        )


@dataclass(frozen=True)
class SyntheticMaster:
    reference_catalog: tuple[MasterReferenceRecord, ...]
    sites: tuple[dict[str, Any], ...]
    products: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class SyntheticRawSources:
    electricity_rows: tuple[RawElectricityRow, ...]


@dataclass(frozen=True)
class SyntheticLoadedSource:
    source_ref: str
    role: str
    path: str
    media_type: str
    schema_id: str
    row_count: int
    content_digest: str

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "role": self.role,
            "path": self.path,
            "media_type": self.media_type,
            "schema_id": self.schema_id,
            "row_count": self.row_count,
            "content_digest": self.content_digest,
        }


@dataclass(frozen=True)
class SyntheticInputBundle:
    config: SyntheticScenarioConfig
    manifest: dict[str, Any]
    master: SyntheticMaster
    raw_sources: SyntheticRawSources
    output_contract: tuple[str, ...] = OUTPUT_CONTRACT
    loaded_sources: tuple[SyntheticLoadedSource, ...] = ()


@dataclass(frozen=True)
class SyntheticOracle:
    expected_claims: tuple[ExpectedClaim, ...]
    expected_derived_claims: tuple[ExpectedDerivedClaim, ...]
    expected_obligations: tuple[ExpectedObligation, ...]
    expected_hazards: tuple[ExpectedHazard, ...]
    expected_failed_claims: tuple[ExpectedFailedClaim, ...]
    injected_anomalies: tuple[InjectedAnomaly, ...]
    source_to_expected_claim_map: tuple[ExpectedSourceMap, ...]
    expected_receipt: ExpectedReceipt | None = None


@dataclass(frozen=True)
class SyntheticRun:
    config: SyntheticScenarioConfig
    manifest: dict[str, Any]
    master: SyntheticMaster
    raw_sources: SyntheticRawSources
    oracle: SyntheticOracle
    output_contract: tuple[str, ...] = OUTPUT_CONTRACT

    @property
    def input_bundle(self) -> SyntheticInputBundle:
        return SyntheticInputBundle(
            config=self.config,
            manifest=self.manifest,
            master=self.master,
            raw_sources=self.raw_sources,
            output_contract=self.output_contract,
            loaded_sources=build_synthetic_loaded_sources(
                self.manifest,
                master=self.master,
                raw_sources=self.raw_sources,
            ),
        )


def generate_synthetic_pcf_run(config: SyntheticScenarioConfig) -> SyntheticRun:
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


def write_synthetic_run(run: SyntheticRun, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "master").mkdir(exist_ok=True)
    (run_dir / "raw_sources").mkdir(exist_ok=True)
    (run_dir / "oracle").mkdir(exist_ok=True)

    _write_json(run_dir / "manifest.json", run.manifest)
    _write_csv(
        run_dir / "master" / "reference_catalog.csv",
        [
            "reference_id",
            "reference_type",
            "label",
            "geography",
            "valid_period",
            "method",
            "factor_value",
            "input_unit",
            "output_unit",
            "source",
            "witness_id",
        ],
        (record.to_row() for record in run.master.reference_catalog),
    )
    _write_csv(
        run_dir / "master" / "sites.csv",
        ["site_id", "site_name", "geography"],
        run.master.sites,
    )
    _write_csv(
        run_dir / "master" / "products.csv",
        ["product_id", "site_id"],
        run.master.products,
    )
    _write_csv(
        run_dir / "raw_sources" / "erp_electricity.csv",
        [
            "source_row_id",
            "source_ref",
            "period",
            "site_id",
            "site_name",
            "product_id",
            "activity_type",
            "amount",
            "unit",
        ],
        (row.to_row() for row in run.raw_sources.electricity_rows),
    )
    _write_csv(
        run_dir / "oracle" / "expected_claims.csv",
        ["claim_id", "field", "value", "unit", "witness_id", "source_row_id"],
        (claim.to_row() for claim in run.oracle.expected_claims),
    )
    _write_csv(
        run_dir / "oracle" / "expected_derived_claims.csv",
        ["claim_id", "field", "value", "unit", "formula_id"],
        (claim.to_row() for claim in run.oracle.expected_derived_claims),
    )
    _write_csv(
        run_dir / "oracle" / "expected_obligations.csv",
        ["obligation_id", "kind", "field", "reason"],
        (obligation.to_row() for obligation in run.oracle.expected_obligations),
    )
    _write_csv(
        run_dir / "oracle" / "expected_hazards.csv",
        ["hazard_id", "kind", "field", "severity"],
        (hazard.to_row() for hazard in run.oracle.expected_hazards),
    )
    _write_csv(
        run_dir / "oracle" / "expected_failed_claims.csv",
        ["failed_claim_id", "field", "value", "reason", "source_row_id"],
        (claim.to_row() for claim in run.oracle.expected_failed_claims),
    )
    _write_csv(
        run_dir / "oracle" / "injected_anomalies.csv",
        ["anomaly_id", "anomaly_type", "source_row_id", "field", "description"],
        (anomaly.to_row() for anomaly in run.oracle.injected_anomalies),
    )
    _write_csv(
        run_dir / "oracle" / "source_to_expected_claim_map.csv",
        [
            "source_ref",
            "source_row_id",
            "expected_claim_id",
            "expected_field",
            "witness_id",
        ],
        (item.to_row() for item in run.oracle.source_to_expected_claim_map),
    )
    if run.oracle.expected_receipt is not None:
        _write_json(
            run_dir / "oracle" / "expected_receipt.json",
            run.oracle.expected_receipt.to_payload(),
        )
    return run_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    headers: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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
) -> ExpectedReceipt:
    commit_package_id = f"commit-package:{config.subject_id}"
    governance_decision_id = f"governance-decision:{commit_package_id}"
    manifest_dependency_id = _synthetic_manifest_dependency_id(config)
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


def synthetic_source_input_dependency_id(
    config: SyntheticScenarioConfig,
    *,
    role: str,
    source_ref: str,
) -> str:
    return (
        f"{SYNTHETIC_SOURCE_INPUT_KIND}:{config.scenario_id}:"
        f"seed-{config.seed}:{role}:{source_ref}"
    )


def build_synthetic_loaded_source(
    *,
    source_ref: str,
    role: str,
    path: str,
    media_type: str,
    schema_id: str,
    rows: Iterable[dict[str, Any]],
) -> SyntheticLoadedSource:
    canonical_rows = tuple(dict(row) for row in rows)
    return SyntheticLoadedSource(
        source_ref=source_ref,
        role=role,
        path=path,
        media_type=media_type,
        schema_id=schema_id,
        row_count=len(canonical_rows),
        content_digest=_synthetic_source_content_digest(canonical_rows),
    )


def build_synthetic_loaded_sources(
    manifest: dict[str, Any],
    *,
    master: SyntheticMaster,
    raw_sources: SyntheticRawSources,
) -> tuple[SyntheticLoadedSource, ...]:
    return tuple(
        build_synthetic_loaded_source(
            source_ref=str(source["source_ref"]),
            role=str(source["role"]),
            path=str(source["path"]),
            media_type=str(source["media_type"]),
            schema_id=str(source["schema_id"]),
            rows=_source_rows_for_manifest_source(
                master,
                raw_sources,
                role=str(source["role"]),
                source_ref=str(source["source_ref"]),
            ),
        )
        for source in manifest.get("sources", ())
        if isinstance(source, dict)
    )


def _source_rows_for_manifest_source(
    master: SyntheticMaster,
    raw_sources: SyntheticRawSources,
    *,
    role: str,
    source_ref: str,
) -> tuple[dict[str, Any], ...]:
    if role == "master_reference_catalog":
        return tuple(record.to_row() for record in master.reference_catalog)
    if role == "master_sites":
        return tuple(dict(row) for row in master.sites)
    if role == "master_products":
        return tuple(dict(row) for row in master.products)
    if role == "raw_source":
        return tuple(
            row.to_row()
            for row in raw_sources.electricity_rows
            if row.source_ref == source_ref
        )
    return ()


def _synthetic_source_content_digest(rows: tuple[dict[str, Any], ...]) -> str:
    encoded = json.dumps(
        {"rows": rows},
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _synthetic_source_dependency_refs(
    config: SyntheticScenarioConfig,
) -> tuple[ExpectedDependencyRef, ...]:
    return tuple(
        ExpectedDependencyRef(
            dependency_kind=SYNTHETIC_SOURCE_INPUT_KIND,
            dependency_id=synthetic_source_input_dependency_id(
                config,
                role=role,
                source_ref=source_ref,
            ),
        )
        for role, source_ref in _synthetic_source_identities(config)
    )


def _synthetic_source_identities(
    config: SyntheticScenarioConfig,
) -> tuple[tuple[str, str], ...]:
    return (
        ("master_reference_catalog", "reference_catalog.csv"),
        ("master_sites", "sites.csv"),
        ("master_products", "products.csv"),
        ("raw_source", config.source_ref),
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
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "OUTPUT_CONTRACT",
    "RawElectricityRow",
    "SYNTHETIC_SOURCE_INPUT_KIND",
    "SyntheticLoadedSource",
    "SyntheticInputBundle",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticRawSources",
    "SyntheticRun",
    "build_synthetic_loaded_source",
    "build_synthetic_loaded_sources",
    "generate_synthetic_pcf_run",
    "synthetic_source_input_dependency_id",
    "write_synthetic_run",
]
