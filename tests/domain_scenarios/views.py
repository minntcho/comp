from __future__ import annotations

from typing import Any


def scenario_result_view(result) -> dict[str, Any]:
    return {
        "scenario_id": result.scenario_id,
        "resolver_steps": result.resolver_steps,
        "report": report_view(result.report),
        "commit": commit_view(result.preparation),
        "receipt_trace": receipt_trace_view(
            result.preparation.receipt,
        ),
        "replay_trace": replay_trace_view(result),
        "proof_graph": proof_graph_view(result),
        "facts": {
            "report_count": len(result.report_facts),
            "commit_count": len(result.commit_facts),
        },
        "projection": result.projection,
    }


def report_view(report) -> dict[str, Any]:
    from comp.views import validation_summary_view

    return {
        "status": report.status,
        "friendly_summary": validation_summary_view(report),
        "open_obligations": [
            _obligation_view(obligation)
            for obligation in report.obligations
        ],
        "resolved_obligations": [
            _obligation_view(obligation)
            for obligation in report.resolved_obligations
        ],
        "reference_candidates": [
            {
                "candidate_id": candidate.candidate_id,
                "reference_id": candidate.reference_id,
                "reference_type": candidate.reference_type,
                "retrieval_method": candidate.retrieval_method,
                "retrieval_score": candidate.retrieval_score,
                "authority": candidate.authority,
            }
            for candidate in report.reference_candidates
        ],
        "reference_bindings": [
            {
                "binding_id": binding.binding_id,
                "reference_id": binding.reference_id,
                "selected_candidate_id": binding.selected_candidate_id,
                "rejected_candidates": [
                    {
                        "reference_id": rejected.reference_id,
                        "reason": rejected.reason,
                    }
                    for rejected in binding.rejected_candidates
                ],
            }
            for binding in report.reference_bindings
        ],
        "derived_claims": [
            {
                "claim_id": claim.claim_id,
                "field": claim.field,
                "value": claim.value,
                "unit": claim.unit,
                "trace_id": claim.trace.trace_id,
                "formula_id": claim.formula_id,
                "reference_binding_ids": claim.trace.reference_binding_ids,
            }
            for claim in report.derived_claims
        ],
    }


def commit_view(preparation) -> dict[str, Any]:
    return {
        "package_id": preparation.package.package_id,
        "package_complete": preparation.package.complete,
        "governance_status": preparation.decision.status,
        "receipt_id": (
            preparation.receipt.public_row_id
            if preparation.receipt is not None
            else None
        ),
    }


def receipt_trace_view(receipt) -> dict[str, Any] | None:
    if receipt is None or receipt.citations is None:
        return None

    citations = receipt.citations
    return {
        "reference_binding_ids": citations.reference_binding_ids,
        "derived_claim_ids": citations.derived_claim_ids,
        "calculation_trace_ids": citations.calculation_trace_ids,
        "formula_ids": citations.formula_ids,
        "value_commitments": [
            {
                "field": commitment.field,
                "source_kind": commitment.source_kind,
                "source_id": commitment.source_id,
                "value_digest": commitment.value_digest,
                "digest_alg": commitment.digest_alg,
            }
            for commitment in citations.projection_value_commitments
        ],
        "dependency_fingerprints": [
            {
                "dependency_kind": fingerprint.dependency_kind,
                "dependency_id": fingerprint.dependency_id,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
            }
            for fingerprint in citations.dependency_fingerprints
        ],
    }


def replay_trace_view(result) -> dict[str, Any] | None:
    receipt = result.preparation.receipt
    if receipt is None or result.projection is None:
        return None

    from comp import PublicOutputSpec
    from comp.persistence import ProjectionReplayBlocked
    from tests.domain_scenarios.persistence import (
        replay_scenario_projection,
        scenario_replay_bundle,
    )

    bundle = scenario_replay_bundle(result)
    try:
        replay = replay_scenario_projection(
            result,
            PublicOutputSpec(receipt.projection_id, tuple(result.projection.keys())),
            bundle=bundle,
        )
    except ProjectionReplayBlocked as exc:
        return {
            "status": "blocked",
            "reason": str(exc),
        }

    return {
        "status": "replayed",
        "receipt_key": {
            "public_row_id": replay.receipt_key.public_row_id,
            "projection_id": replay.receipt_key.projection_id,
            "draft_id": replay.receipt_key.draft_id,
        },
        "projection_id": replay.projection_id,
        "artifact_refs": [
            {
                "artifact_id": ref.artifact_id,
                "artifact_kind": ref.artifact_kind,
            }
            for ref in replay.artifact_refs
        ],
        "artifact_digests": [
            {
                "artifact_id": artifact_id,
                "body_digest": body_digest,
            }
            for artifact_id, body_digest in replay.artifact_digests
        ],
        "dependency_manifests": _dependency_manifests_view(
            replay.dependency_fingerprints,
            bundle.artifacts,
        ),
    }


def proof_graph_view(result) -> dict[str, Any] | None:
    receipt = result.preparation.receipt
    if receipt is None or result.projection is None:
        return None

    from comp import PublicOutputSpec
    from comp.explanation import export_receipt_proof_graph
    from comp.persistence import ProjectionReplayBlocked
    from tests.domain_scenarios.persistence import (
        replay_scenario_projection,
        scenario_replay_bundle,
    )

    bundle = scenario_replay_bundle(result)
    try:
        replay = replay_scenario_projection(
            result,
            PublicOutputSpec(receipt.projection_id, tuple(result.projection.keys())),
            bundle=bundle,
        )
    except ProjectionReplayBlocked:
        return None

    return export_receipt_proof_graph(
        receipt=receipt,
        replay=replay,
        artifacts=bundle.artifacts,
    ).to_payload()


def _dependency_manifests_view(fingerprints, artifacts) -> dict[str, list[dict[str, Any]]]:
    profile_locks = []
    catalog_snapshots = []
    reference_records = []
    for fingerprint in fingerprints:
        envelope = artifacts.get(fingerprint.dependency_id)
        if fingerprint.dependency_kind == "compiler_profile":
            profile_lock = envelope.body.get("profile_lock")
            if isinstance(profile_lock, dict):
                profile_locks.append(
                    {
                        "profile_id": profile_lock["profile_id"],
                        "active_rule_count": len(profile_lock["active_rule_ids"]),
                        "active_rubric_count": len(
                            profile_lock["active_rubric_ids"]
                        ),
                        "active_retrieval_policy_count": len(
                            profile_lock["active_retrieval_policy_ids"]
                        ),
                        "domain_pack_count": len(profile_lock["domain_packs"]),
                    }
                )
        elif fingerprint.dependency_kind == "reference_catalog_snapshot":
            selected = envelope.body.get(
                "record_fingerprints",
                envelope.body.get("selected_record_fingerprints", ()),
            )
            catalog_snapshots.append(
                {
                    "snapshot_id": fingerprint.dependency_id,
                    "catalog_id": envelope.body.get("catalog_id"),
                    "version": envelope.body.get(
                        "catalog_version",
                        envelope.body.get("version"),
                    ),
                    "selected_record_count": len(selected),
                }
            )
        elif fingerprint.dependency_kind == "reference_record":
            reference_records.append(
                {
                    "reference_id": fingerprint.dependency_id,
                }
            )
    return {
        "profile_locks": profile_locks,
        "catalog_snapshots": catalog_snapshots,
        "reference_records": reference_records,
    }


def _obligation_view(obligation) -> dict[str, str | None]:
    return {
        "obligation_id": obligation.obligation_id,
        "kind": obligation.kind,
        "field": obligation.field,
        "reason": obligation.reason,
    }


__all__ = [
    "commit_view",
    "proof_graph_view",
    "receipt_trace_view",
    "replay_trace_view",
    "report_view",
    "scenario_result_view",
]
