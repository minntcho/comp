from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from comp.judgment import CommitReceipt
from comp.persistence import (
    ArtifactRef,
    InMemoryArtifactStore,
    ProjectionReplayReport,
    ReceiptLedgerKey,
)
from comp.persistence.envelope import ArtifactEnvelope


class ProofGraphExportError(RuntimeError):
    """Raised when a replay report cannot be normalized into a proof graph."""


@dataclass(frozen=True, slots=True)
class ProofNode:
    node_id: str
    node_kind: str
    label: str
    digest: str | None = None
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("node_id", self.node_id)
        _require_non_empty("node_kind", self.node_kind)
        _require_non_empty("label", self.label)

    def to_payload(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "node_kind": self.node_kind,
            "label": self.label,
            "digest": self.digest,
            "metadata": _metadata_payload(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ProofEdge:
    source_id: str
    target_id: str
    edge_kind: str
    metadata: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_non_empty("source_id", self.source_id)
        _require_non_empty("target_id", self.target_id)
        _require_non_empty("edge_kind", self.edge_kind)

    def to_payload(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_kind": self.edge_kind,
            "metadata": _metadata_payload(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ReceiptProofGraph:
    public_row_id: str
    projection_id: str
    receipt_node_id: str
    replay_receipt_key: ReceiptLedgerKey
    nodes: tuple[ProofNode, ...]
    edges: tuple[ProofEdge, ...]
    field_paths: tuple[tuple[str, tuple[str, ...]], ...] = field(default_factory=tuple)
    authority: str = "explanation_only"
    can_authorize_public_projection: bool = False

    def node(self, node_id: str) -> ProofNode | None:
        for graph_node in self.nodes:
            if graph_node.node_id == node_id:
                return graph_node
        return None

    def artifact_node(self, artifact_ref: ArtifactRef) -> ProofNode | None:
        return self.node(
            artifact_node_id(artifact_ref.artifact_kind, artifact_ref.artifact_id)
        )

    def field_node(self, field: str) -> ProofNode | None:
        return self.node(
            public_field_node_id(self.public_row_id, self.projection_id, field)
        )

    def edges_between(
        self,
        source_id: str,
        target_id: str,
        *,
        edge_kind: str | None = None,
    ) -> tuple[ProofEdge, ...]:
        return tuple(
            edge
            for edge in self.edges
            if edge.source_id == source_id
            and edge.target_id == target_id
            and (edge_kind is None or edge.edge_kind == edge_kind)
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "public_row_id": self.public_row_id,
            "projection_id": self.projection_id,
            "receipt_node_id": self.receipt_node_id,
            "replay_receipt_key": {
                "public_row_id": self.replay_receipt_key.public_row_id,
                "projection_id": self.replay_receipt_key.projection_id,
                "draft_id": self.replay_receipt_key.draft_id,
            },
            "authority": self.authority,
            "can_authorize_public_projection": self.can_authorize_public_projection,
            "nodes": tuple(node.to_payload() for node in self.nodes),
            "edges": tuple(edge.to_payload() for edge in self.edges),
            "field_paths": tuple(
                {"field": field, "node_ids": node_ids}
                for field, node_ids in self.field_paths
            ),
        }


def export_receipt_proof_graph(
    *,
    receipt: CommitReceipt,
    replay: ProjectionReplayReport,
    artifacts: InMemoryArtifactStore,
) -> ReceiptProofGraph:
    """Export an explanation-only graph from an already successful replay.

    The exporter is read-only. It consumes the receipt, replay report, and
    replayed artifact envelopes; it does not call the compiler, projection gate,
    governance gate, resolver, calculator, or replay function.
    """

    _validate_replay_scope(receipt, replay)
    builder = _ReceiptProofGraphBuilder(
        receipt=receipt,
        replay=replay,
        artifacts=artifacts,
    )
    return builder.export()


def receipt_node_id(receipt: CommitReceipt) -> str:
    return (
        "commit_receipt:"
        f"{receipt.public_row_id}:{receipt.projection_id}:{receipt.draft_id}"
    )


def public_projection_node_id(public_row_id: str, projection_id: str) -> str:
    return f"public_projection:{public_row_id}:{projection_id}"


def public_field_node_id(public_row_id: str, projection_id: str, field: str) -> str:
    return f"public_field:{public_row_id}:{projection_id}:{field}"


def artifact_node_id(artifact_kind: str, artifact_id: str) -> str:
    return f"{artifact_kind}:{artifact_id}"


def dependency_fingerprint_node_id(
    dependency_kind: str,
    dependency_id: str,
) -> str:
    return f"dependency_fingerprint:{dependency_kind}:{dependency_id}"


class _ReceiptProofGraphBuilder:
    def __init__(
        self,
        *,
        receipt: CommitReceipt,
        replay: ProjectionReplayReport,
        artifacts: InMemoryArtifactStore,
    ) -> None:
        self._receipt = receipt
        self._replay = replay
        self._artifacts = artifacts
        self._nodes: dict[str, ProofNode] = {}
        self._edges: dict[tuple[str, str, str, tuple[tuple[str, Any], ...]], ProofEdge] = {}
        self._artifact_envelopes: dict[tuple[str, str], ArtifactEnvelope] = {}
        self._field_paths: dict[str, tuple[str, ...]] = {}

    def export(self) -> ReceiptProofGraph:
        self._add_receipt_node()
        self._add_public_projection_nodes()
        self._add_artifact_nodes()
        self._add_dependency_fingerprint_nodes()
        self._add_receipt_citation_edges()
        self._add_public_projection_edges()
        return ReceiptProofGraph(
            public_row_id=self._receipt.public_row_id,
            projection_id=self._receipt.projection_id,
            receipt_node_id=receipt_node_id(self._receipt),
            replay_receipt_key=self._replay.receipt_key,
            nodes=tuple(self._nodes.values()),
            edges=tuple(self._edges.values()),
            field_paths=tuple(sorted(self._field_paths.items())),
        )

    def _add_receipt_node(self) -> None:
        self._add_node(
            ProofNode(
                node_id=receipt_node_id(self._receipt),
                node_kind="commit_receipt",
                label=f"Commit receipt: {self._receipt.public_row_id}",
                metadata=_metadata(
                    public_row_id=self._receipt.public_row_id,
                    projection_id=self._receipt.projection_id,
                    draft_id=self._receipt.draft_id,
                    authorized_fields=self._receipt.authorized_fields,
                ),
            )
        )

    def _add_public_projection_nodes(self) -> None:
        projection_node_id = public_projection_node_id(
            self._receipt.public_row_id,
            self._receipt.projection_id,
        )
        self._add_node(
            ProofNode(
                node_id=projection_node_id,
                node_kind="public_projection",
                label=f"Public projection: {self._receipt.projection_id}",
                metadata=_metadata(
                    public_row_id=self._receipt.public_row_id,
                    projection_id=self._receipt.projection_id,
                    field_count=len(self._replay.public_row),
                ),
            )
        )
        for field in self._replay.public_row:
            self._add_node(
                ProofNode(
                    node_id=public_field_node_id(
                        self._receipt.public_row_id,
                        self._receipt.projection_id,
                        field,
                    ),
                    node_kind="public_field",
                    label=f"Public field: {field}",
                    metadata=_metadata(
                        field=field,
                        projection_id=self._receipt.projection_id,
                        has_value_commitment=field in _commitments_by_field(
                            self._receipt
                        ),
                    ),
                )
            )

    def _add_artifact_nodes(self) -> None:
        for ref in self._replay.artifact_refs:
            envelope = self._artifact_envelope(ref)
            self._add_node(
                ProofNode(
                    node_id=artifact_node_id(ref.artifact_kind, ref.artifact_id),
                    node_kind=ref.artifact_kind,
                    label=_artifact_label(ref, envelope),
                    digest=envelope.body_digest,
                    metadata=_artifact_metadata(ref, envelope),
                )
            )

    def _add_dependency_fingerprint_nodes(self) -> None:
        for fingerprint in self._replay.dependency_fingerprints:
            self._add_node(
                ProofNode(
                    node_id=dependency_fingerprint_node_id(
                        fingerprint.dependency_kind,
                        fingerprint.dependency_id,
                    ),
                    node_kind="dependency_fingerprint",
                    label=(
                        "Dependency fingerprint: "
                        f"{fingerprint.dependency_kind}:{fingerprint.dependency_id}"
                    ),
                    digest=fingerprint.fingerprint,
                    metadata=_metadata(
                        dependency_kind=fingerprint.dependency_kind,
                        dependency_id=fingerprint.dependency_id,
                        digest_alg=fingerprint.digest_alg,
                    ),
                )
            )

    def _add_receipt_citation_edges(self) -> None:
        citations = self._receipt.citations
        if citations is None:
            return
        receipt_id = receipt_node_id(self._receipt)
        package_node_id = artifact_node_id("commit_package", citations.commit_package_id)
        self._add_edge(package_node_id, receipt_id, "committed_in")
        self._add_edge(
            artifact_node_id("governance_decision", citations.governance_decision_id),
            receipt_id,
            "decided_by",
            governance_status=citations.governance_status,
        )
        for commitment in citations.projection_value_commitments:
            self._add_edge(
                artifact_node_id(commitment.source_kind, commitment.source_id),
                package_node_id,
                "committed_in",
                field=commitment.field,
                source_kind=commitment.source_kind,
            )
        for fingerprint in citations.dependency_fingerprints:
            self._add_edge(
                receipt_id,
                dependency_fingerprint_node_id(
                    fingerprint.dependency_kind,
                    fingerprint.dependency_id,
                ),
                "pinned_dependency",
                dependency_kind=fingerprint.dependency_kind,
                dependency_id=fingerprint.dependency_id,
            )

    def _add_public_projection_edges(self) -> None:
        projection_node_id = public_projection_node_id(
            self._receipt.public_row_id,
            self._receipt.projection_id,
        )
        receipt_id = receipt_node_id(self._receipt)
        self._add_edge(projection_node_id, receipt_id, "authorized_by")
        commitments = _commitments_by_field(self._receipt)
        for field in self._replay.public_row:
            field_node_id = public_field_node_id(
                self._receipt.public_row_id,
                self._receipt.projection_id,
                field,
            )
            path = [field_node_id, projection_node_id, receipt_id]
            self._add_edge(field_node_id, projection_node_id, "projected_as", field=field)
            self._add_edge(field_node_id, receipt_id, "authorized_by", field=field)
            commitment = commitments.get(field)
            if commitment is not None:
                source_node_id = artifact_node_id(
                    commitment.source_kind,
                    commitment.source_id,
                )
                if source_node_id in self._nodes:
                    self._add_edge(
                        source_node_id,
                        field_node_id,
                        "projected_as",
                        field=field,
                        value_digest=commitment.value_digest,
                        digest_alg=commitment.digest_alg,
                    )
                    path.insert(0, source_node_id)
            self._field_paths[field] = tuple(path)

    def _artifact_envelope(self, ref: ArtifactRef) -> ArtifactEnvelope:
        key = (ref.artifact_kind, ref.artifact_id)
        envelope = self._artifact_envelopes.get(key)
        if envelope is not None:
            return envelope
        try:
            envelope = self._artifacts.get(ref.artifact_id)
        except KeyError as exc:
            raise ProofGraphExportError(
                f"Proof graph missing replay artifact: {ref.artifact_id}."
            ) from exc
        if envelope.artifact_kind != ref.artifact_kind:
            raise ProofGraphExportError(
                f"Proof graph artifact kind mismatch: {ref.artifact_id}."
            )
        self._artifact_envelopes[key] = envelope
        return envelope

    def _add_node(self, node: ProofNode) -> None:
        existing = self._nodes.get(node.node_id)
        if existing is None:
            self._nodes[node.node_id] = node
            return
        if existing != node:
            raise ProofGraphExportError(
                f"Proof graph node id conflict: {node.node_id}."
            )

    def _add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_kind: str,
        **metadata: Any,
    ) -> None:
        if source_id not in self._nodes or target_id not in self._nodes:
            return
        edge_metadata = _metadata(**metadata)
        edge = ProofEdge(
            source_id=source_id,
            target_id=target_id,
            edge_kind=edge_kind,
            metadata=edge_metadata,
        )
        self._edges[(source_id, target_id, edge_kind, edge_metadata)] = edge


def _validate_replay_scope(
    receipt: CommitReceipt,
    replay: ProjectionReplayReport,
) -> None:
    expected = ReceiptLedgerKey.from_receipt(receipt)
    if replay.receipt_key != expected:
        raise ProofGraphExportError("Proof graph receipt key does not match replay report.")
    if replay.projection_id != receipt.projection_id:
        raise ProofGraphExportError("Proof graph projection id does not match receipt.")


def _artifact_label(ref: ArtifactRef, envelope: ArtifactEnvelope) -> str:
    body = envelope.body
    field = body.get("field")
    if isinstance(field, str):
        return f"{ref.artifact_kind}: {field}"
    for key in (
        "claim_id",
        "decision_id",
        "package_id",
        "dependency_id",
        "snapshot_id",
        "witness_id",
    ):
        value = body.get(key)
        if isinstance(value, str):
            return f"{ref.artifact_kind}: {value}"
    return f"{ref.artifact_kind}: {ref.artifact_id}"


def _artifact_metadata(
    ref: ArtifactRef,
    envelope: ArtifactEnvelope,
) -> tuple[tuple[str, Any], ...]:
    metadata: dict[str, Any] = {
        "artifact_id": ref.artifact_id,
        "artifact_kind": ref.artifact_kind,
        "schema_version": envelope.schema_version,
    }
    metadata.update(_safe_body_metadata(envelope.body))
    return tuple(sorted(metadata.items()))


def _safe_body_metadata(body: Mapping[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for key, value in body.items():
        if key in _SENSITIVE_BODY_KEYS:
            metadata[f"has_{key}"] = value is not None
            continue
        if key == "steps":
            metadata["step_count"] = len(_sequence_or_empty(value))
            continue
        if key == "record_fingerprints":
            metadata["record_fingerprint_count"] = len(_sequence_or_empty(value))
            continue
        if key == "profile_lock":
            metadata["has_profile_lock"] = value is not None
            continue
        if _is_safe_metadata_value(value):
            metadata[key] = value
    return metadata


def _is_safe_metadata_value(value: Any) -> bool:
    if value is None or isinstance(value, str | int | float | bool):
        return True
    if isinstance(value, tuple):
        return all(_is_safe_metadata_value(item) for item in value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return all(_is_safe_metadata_value(item) for item in value)
    if isinstance(value, Mapping):
        return all(
            isinstance(key, str) and _is_safe_metadata_value(item)
            for key, item in value.items()
        )
    return False


def _commitments_by_field(receipt: CommitReceipt):
    if receipt.citations is None:
        return {}
    return {
        commitment.field: commitment
        for commitment in receipt.citations.projection_value_commitments
    }


def _metadata(**items: Any) -> tuple[tuple[str, Any], ...]:
    return tuple(
        (key, value)
        for key, value in sorted(items.items())
        if value is not None
    )


def _metadata_payload(metadata: tuple[tuple[str, Any], ...]) -> dict[str, Any]:
    return {key: _jsonable(value) for key, value in metadata}


def _jsonable(value: Any) -> Any:
    if isinstance(value, tuple):
        return tuple(_jsonable(item) for item in value)
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(_jsonable(item) for item in value)
    return value


def _sequence_or_empty(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _require_non_empty(field: str, value: str) -> None:
    if not value:
        raise ValueError(f"{field} is required.")


_SENSITIVE_BODY_KEYS = frozenset({"value", "output_value", "text"})


__all__ = [
    "ProofEdge",
    "ProofGraphExportError",
    "ProofNode",
    "ReceiptProofGraph",
    "artifact_node_id",
    "dependency_fingerprint_node_id",
    "export_receipt_proof_graph",
    "public_field_node_id",
    "public_projection_node_id",
    "receipt_node_id",
]
