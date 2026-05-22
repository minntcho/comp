from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from comp.compiler_tool import (
    CommitPreparation,
    ValidationReport,
)
from comp.judgment import PublicOutputSpec
from comp.persistence import (
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


@dataclass(frozen=True)
class SyntheticReplayBundle:
    artifacts: InMemoryArtifactStore
    receipt_ledger: InMemoryReceiptLedger


def synthetic_replay_bundle(
    report: ValidationReport,
    preparation: CommitPreparation,
    dependency_artifact_bodies: Mapping[tuple[str, str], Mapping[str, Any]],
) -> SyntheticReplayBundle:
    receipt = preparation.receipt
    if receipt is None:
        raise AssertionError("Synthetic replay requires a commit receipt.")

    artifacts = InMemoryArtifactStore()
    materials = materialize_compiler_run_artifacts(
        report,
        preparation,
        external_material_source=ExternalArtifactMaterialSource.from_bodies(
            dependency_artifact_bodies
        ),
        schema_version="synthetic-scenario-v1",
    )
    build_receipt_envelope_set(receipt, materials, record_to=artifacts)

    receipt_ledger = InMemoryReceiptLedger()
    receipt_ledger.record(receipt)
    return SyntheticReplayBundle(
        artifacts=artifacts,
        receipt_ledger=receipt_ledger,
    )


def replay_synthetic_projection(
    row: Mapping[str, Any],
    projection: PublicOutputSpec,
    preparation: CommitPreparation,
    *,
    bundle: SyntheticReplayBundle,
) -> ProjectionReplayReport:
    receipt = preparation.receipt
    if receipt is None:
        raise AssertionError("Synthetic replay requires a commit receipt.")

    ledger_receipt = bundle.receipt_ledger.get(
        public_row_id=receipt.public_row_id,
        projection_id=receipt.projection_id,
        draft_id=receipt.draft_id,
    )
    return replay_public_projection(
        row,
        projection,
        receipt=ledger_receipt,
        artifacts=bundle.artifacts,
    )


__all__ = [
    "SyntheticReplayBundle",
    "replay_synthetic_projection",
    "synthetic_replay_bundle",
]
