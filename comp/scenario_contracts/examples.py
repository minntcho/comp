from __future__ import annotations

import json
from pathlib import Path

from comp.judgment import (
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputValueCommitment,
)
from comp.persistence import ArtifactEnvelope
from comp.scenario_contracts.artifacts import write_artifact_envelopes
from comp.scenario_contracts.case import (
    RuntimeCase,
    RuntimeProjection,
    write_runtime_case,
)


class ScenarioBundleExistsError(FileExistsError):
    """Raised when scenario init would overwrite an existing bundle."""


def write_public_projection_smoke_bundle(
    path: str | Path,
    *,
    force: bool = False,
) -> Path:
    target = Path(path)
    _ensure_can_write_bundle(target, force=force)
    prepared = target / "prepared"
    prepared.mkdir(parents=True, exist_ok=True)

    public_row = {"site": "plant-a", "amount": 100}
    commitments = (
        PublicOutputValueCommitment.from_value(
            field="site",
            source_kind="checked_claim",
            source_id="checked_claim:site:smoke",
            value=public_row["site"],
        ),
        PublicOutputValueCommitment.from_value(
            field="amount",
            source_kind="checked_claim",
            source_id="checked_claim:amount:smoke",
            value=public_row["amount"],
        ),
    )
    citations = PublicOutputReceiptCitations(
        governance_decision_id="governance_decision:smoke",
        governance_status="commit",
        governance_reasons=("ready",),
        commit_package_id="commit_package:smoke",
        commit_package_complete=True,
        subject_id="facility:smoke",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        profile_id=None,
        report_status="accepted",
        checked_claim_fields=("site", "amount"),
        checked_claim_witness_ids=(),
        semantic_judgment_ids=(),
        reference_binding_ids=(),
        derived_claim_fields=(),
        derived_claim_ids=(),
        calculation_trace_ids=(),
        formula_ids=(),
        resolved_obligation_ids=(),
        open_obligation_ids=(),
        hazard_ids=(),
        projection_value_commitments=commitments,
        dependency_fingerprints=(),
    )
    receipt = PublicOutputReceipt(
        draft_id="draft:smoke",
        winner_receipt_ids=("governance_decision:smoke",),
        barrier_snapshot=citations.to_barrier_snapshot(),
        public_row_id="public-row:smoke",
        projection_id="public-row",
        authorized_fields=("site", "amount"),
        citations=citations,
    )
    write_runtime_case(
        RuntimeCase(
            case_id="public_projection_smoke",
            receipts=(receipt,),
            projections=(
                RuntimeProjection(
                    public_row_id="public-row:smoke",
                    projection_id="public-row",
                    draft_id="draft:smoke",
                    output_fields=("site", "amount"),
                    row=public_row,
                ),
            ),
        ),
        prepared / "runtime_case.json",
    )
    write_artifact_envelopes(
        (
            ArtifactEnvelope.from_body(
                artifact_id="commit_package:smoke",
                artifact_kind="commit_package",
                schema_version="v1",
                body={"package_id": "commit_package:smoke", "complete": True},
            ),
            ArtifactEnvelope.from_body(
                artifact_id="governance_decision:smoke",
                artifact_kind="governance_decision",
                schema_version="v1",
                body={"decision_id": "governance_decision:smoke", "status": "commit"},
            ),
            ArtifactEnvelope.from_body(
                artifact_id="checked_claim:site:smoke",
                artifact_kind="checked_claim",
                schema_version="v1",
                body={
                    "claim_id": "checked_claim:site:smoke",
                    "field": "site",
                    "value": public_row["site"],
                },
            ),
            ArtifactEnvelope.from_body(
                artifact_id="checked_claim:amount:smoke",
                artifact_kind="checked_claim",
                schema_version="v1",
                body={
                    "claim_id": "checked_claim:amount:smoke",
                    "field": "amount",
                    "value": public_row["amount"],
                },
            ),
        ),
        prepared / "artifact_envelopes.jsonl",
    )
    manifest_path = target / "scenario.json"
    manifest_path.write_text(
        json.dumps(_manifest(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path


def _ensure_can_write_bundle(target: Path, *, force: bool) -> None:
    if force or not target.exists():
        return
    if any(target.iterdir()):
        raise ScenarioBundleExistsError(
            f"Scenario bundle target already exists: {target}."
        )


def _manifest() -> dict[str, object]:
    return {
        "id": "public_projection_smoke",
        "input_mode": "canonical_bundle",
        "runtime_case": {"path": "prepared/runtime_case.json"},
        "artifact_envelopes": {"path": "prepared/artifact_envelopes.jsonl"},
        "expected": {
            "invariants": [
                "receipt_exists",
                "replay_succeeds",
                "all_public_rows_have_receipts",
                "projection_values_are_committed",
                "blocking_hazards_absent",
            ]
        },
        "report": {
            "format": "json",
            "path": "reports/latest.json",
        },
    }


__all__ = ["ScenarioBundleExistsError", "write_public_projection_smoke_bundle"]
