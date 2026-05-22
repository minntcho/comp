from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from comp.judgment import PublicOutputSpec
from comp.persistence import (
    ArtifactEnvelope,
    ArtifactRef,
    InMemoryArtifactStore,
    InMemoryReceiptLedger,
    ProjectionReplayReport,
    build_receipt_envelope_set,
    replay_public_projection,
)
from comp.runtime import (
    ExternalArtifactMaterialSource,
    materialize_compiler_run_artifacts,
)
from tests.domain_scenarios.core import DomainScenarioResult


@dataclass(frozen=True)
class DomainScenarioReplayBundle:
    artifacts: InMemoryArtifactStore
    receipt_ledger: InMemoryReceiptLedger


def scenario_replay_bundle(
    result: DomainScenarioResult,
    *,
    skip: ArtifactRef | None = None,
    override: ArtifactEnvelope | None = None,
) -> DomainScenarioReplayBundle:
    receipt = result.preparation.receipt
    if receipt is None:
        raise AssertionError("Scenario replay requires a commit receipt.")

    artifacts = InMemoryArtifactStore()
    materials = materialize_compiler_run_artifacts(
        result.report,
        result.preparation,
        external_material_source=ExternalArtifactMaterialSource.from_bodies(
            _scenario_external_artifact_bodies(result)
        ),
        schema_version="domain-scenario-v1",
    )
    for envelope in build_receipt_envelope_set(receipt, materials):
        ref = ArtifactRef(envelope.artifact_id, envelope.artifact_kind)
        if ref == skip:
            continue
        if override is not None and override.artifact_id == ref.artifact_id:
            artifacts.record(override)
            continue
        artifacts.record(envelope)

    receipt_ledger = InMemoryReceiptLedger()
    receipt_ledger.record(receipt)
    return DomainScenarioReplayBundle(
        artifacts=artifacts,
        receipt_ledger=receipt_ledger,
    )


def replay_scenario_projection(
    result: DomainScenarioResult,
    projection: PublicOutputSpec,
    *,
    bundle: DomainScenarioReplayBundle | None = None,
) -> ProjectionReplayReport:
    receipt = result.preparation.receipt
    if receipt is None:
        raise AssertionError("Scenario replay requires a commit receipt.")
    if result.projection is None:
        raise AssertionError("Scenario replay requires a materialized projection.")

    replay_bundle = bundle or scenario_replay_bundle(result)
    ledger_receipt = replay_bundle.receipt_ledger.get(
        public_row_id=receipt.public_row_id,
        projection_id=receipt.projection_id,
        draft_id=receipt.draft_id,
    )
    return replay_public_projection(
        result.projection,
        projection,
        receipt=ledger_receipt,
        artifacts=replay_bundle.artifacts,
    )


def _scenario_external_artifact_bodies(
    result: DomainScenarioResult,
) -> dict[tuple[str, str], dict[str, Any]]:
    bodies = {
        key: dict(body) for key, body in result.dependency_artifact_bodies.items()
    }
    receipt = result.preparation.receipt
    if receipt is None or receipt.citations is None:
        return bodies

    for judgment_id in receipt.citations.semantic_judgment_ids:
        bodies.setdefault(
            ("semantic_judgment", judgment_id),
            {"judgment_id": judgment_id},
        )

    for witness_id in receipt.citations.checked_claim_witness_ids:
        bodies.setdefault(
            ("evidence_witness", witness_id),
            {"witness_id": witness_id, "source": "domain_scenario"},
        )

    for fingerprint in receipt.citations.dependency_fingerprints:
        key = (fingerprint.dependency_kind, fingerprint.dependency_id)
        if key in bodies:
            continue
        if fingerprint.dependency_kind == "reference_catalog_snapshot":
            bodies[key] = _reference_catalog_snapshot_body(
                fingerprint,
                receipt.citations.dependency_fingerprints,
            )
            continue
        bodies[key] = _dependency_fingerprint_body(fingerprint)
    return bodies


def _reference_catalog_snapshot_body(
    snapshot_fingerprint,
    dependency_fingerprints,
) -> dict[str, Any]:
    catalog_id, catalog_version = _catalog_snapshot_parts(
        snapshot_fingerprint.dependency_id
    )
    body = _dependency_fingerprint_body(snapshot_fingerprint)
    body.update(
        {
            "snapshot_id": snapshot_fingerprint.dependency_id,
            "catalog_id": catalog_id,
            "catalog_version": catalog_version,
            "record_fingerprints": tuple(
                _dependency_fingerprint_body(fingerprint)
                for fingerprint in dependency_fingerprints
                if fingerprint.dependency_kind == "reference_record"
            ),
        }
    )
    return body


def _dependency_fingerprint_body(fingerprint) -> dict[str, str]:
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _catalog_snapshot_parts(snapshot_id: str) -> tuple[str, str]:
    prefix = "reference_catalog_snapshot:"
    if not snapshot_id.startswith(prefix):
        return snapshot_id, ""
    rest = snapshot_id[len(prefix):]
    if ":" not in rest:
        return rest, ""
    catalog_id, catalog_version = rest.rsplit(":", 1)
    return catalog_id, catalog_version


__all__ = [
    "DomainScenarioReplayBundle",
    "replay_scenario_projection",
    "scenario_replay_bundle",
]
