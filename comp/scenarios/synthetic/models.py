from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from comp.scenarios.synthetic.config import SyntheticScenarioConfig


OUTPUT_CONTRACT = ("master", "raw_sources", "oracle")
RESOLUTION_OUTPUT_CONTRACT = (
    "master",
    "raw_sources",
    "resolution_artifacts",
    "oracle",
)
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
class SyntheticResolutionArtifact:
    artifact_id: str
    obligation_id: str
    source_row_id: str
    field: str
    resolved_value: str
    witness_id: str
    source_ref: str
    rationale: str

    def to_row(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "obligation_id": self.obligation_id,
            "source_row_id": self.source_row_id,
            "field": self.field,
            "resolved_value": self.resolved_value,
            "witness_id": self.witness_id,
            "source_ref": self.source_ref,
            "rationale": self.rationale,
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
class ExpectedCalculatedClaim:
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
class ExpectedResolutionArtifact:
    artifact_id: str
    obligation_id: str
    source_row_id: str
    field: str
    resolved_value: str
    witness_id: str
    source_ref: str

    def to_row(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "obligation_id": self.obligation_id,
            "source_row_id": self.source_row_id,
            "field": self.field,
            "resolved_value": self.resolved_value,
            "witness_id": self.witness_id,
            "source_ref": self.source_ref,
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
    resolved_obligation_ids: tuple[str, ...] = ()

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
            "resolved_obligation_ids": list(self.resolved_obligation_ids),
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
            resolved_obligation_ids=tuple(
                payload.get("resolved_obligation_ids", ())
            ),
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
class SyntheticResolutionArtifacts:
    unit_witnesses: tuple[SyntheticResolutionArtifact, ...] = ()


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
    resolution_artifacts: SyntheticResolutionArtifacts = SyntheticResolutionArtifacts()
    output_contract: tuple[str, ...] = OUTPUT_CONTRACT
    loaded_sources: tuple[SyntheticLoadedSource, ...] = ()


@dataclass(frozen=True)
class SyntheticOracle:
    expected_claims: tuple[ExpectedClaim, ...]
    expected_calculated_claims: tuple[ExpectedCalculatedClaim, ...]
    expected_validation_requirements: tuple[ExpectedObligation, ...]
    expected_hazards: tuple[ExpectedHazard, ...]
    expected_failed_claims: tuple[ExpectedFailedClaim, ...]
    injected_anomalies: tuple[InjectedAnomaly, ...]
    source_to_expected_claim_map: tuple[ExpectedSourceMap, ...]
    expected_resolved_validation_requirements: tuple[ExpectedObligation, ...] | None = None
    expected_resolution_artifacts: tuple[ExpectedResolutionArtifact, ...] | None = None
    expected_receipt: ExpectedReceipt | None = None


@dataclass(frozen=True)
class SyntheticRun:
    config: SyntheticScenarioConfig
    manifest: dict[str, Any]
    master: SyntheticMaster
    raw_sources: SyntheticRawSources
    oracle: SyntheticOracle
    resolution_artifacts: SyntheticResolutionArtifacts = SyntheticResolutionArtifacts()
    output_contract: tuple[str, ...] = OUTPUT_CONTRACT

    @property
    def input_bundle(self) -> SyntheticInputBundle:
        from comp.scenarios.synthetic.sources import build_synthetic_loaded_sources

        return SyntheticInputBundle(
            config=self.config,
            manifest=self.manifest,
            master=self.master,
            raw_sources=self.raw_sources,
            resolution_artifacts=self.resolution_artifacts,
            output_contract=self.output_contract,
            loaded_sources=build_synthetic_loaded_sources(
                self.manifest,
                master=self.master,
                raw_sources=self.raw_sources,
                resolution_artifacts=self.resolution_artifacts,
            ),
        )


__all__ = [
    "ExpectedArtifactRef",
    "ExpectedClaim",
    "ExpectedDependencyRef",
    "ExpectedCalculatedClaim",
    "ExpectedFailedClaim",
    "ExpectedHazard",
    "ExpectedObligation",
    "ExpectedReceipt",
    "ExpectedResolutionArtifact",
    "ExpectedSourceMap",
    "InjectedAnomaly",
    "MasterReferenceRecord",
    "OUTPUT_CONTRACT",
    "RawElectricityRow",
    "RESOLUTION_OUTPUT_CONTRACT",
    "SYNTHETIC_SOURCE_INPUT_KIND",
    "SyntheticInputBundle",
    "SyntheticLoadedSource",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticRawSources",
    "SyntheticResolutionArtifact",
    "SyntheticResolutionArtifacts",
    "SyntheticRun",
]
