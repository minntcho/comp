from dataclasses import replace

from comp.explanation import (
    ProofGraphExportError,
    ReceiptProofGraph,
    artifact_node_id,
    dependency_fingerprint_node_id,
    export_receipt_proof_graph,
    public_field_node_id,
    public_projection_node_id,
    receipt_node_id,
)
from comp.persistence import replay_public_projection
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)


def test_receipt_proof_graph_exports_successful_replay_payload():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )

    graph = export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )

    assert isinstance(graph, ReceiptProofGraph)
    assert graph.authority == "explanation_only"
    assert graph.can_authorize_public_projection is False
    assert graph.receipt_node_id == receipt_node_id(case.receipt)
    assert graph.to_payload()["authority"] == "explanation_only"
    assert graph.to_payload()["can_authorize_public_projection"] is False
    for artifact_ref in replay.artifact_refs:
        assert graph.artifact_node(artifact_ref) is not None


def test_public_projection_fields_connect_to_receipt_and_value_sources():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )

    graph = export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )

    receipt_id = receipt_node_id(case.receipt)
    projection_id = public_projection_node_id("public-row-1", "public-row")
    amount_field_id = public_field_node_id("public-row-1", "public-row", "amount")
    amount_claim_id = artifact_node_id(
        "checked_claim",
        "checked_claim:amount:span-amount",
    )

    assert graph.field_node("amount") is not None
    assert _has_edge(graph, amount_field_id, projection_id, "projected_as")
    assert _has_edge(graph, amount_field_id, receipt_id, "authorized_by")
    assert _has_edge(graph, amount_claim_id, amount_field_id, "projected_as")
    assert dict(graph.field_paths)["amount"] == (
        amount_claim_id,
        amount_field_id,
        projection_id,
        receipt_id,
    )


def test_dependency_fingerprints_are_explanation_nodes():
    case = receipt_projection_case(amount=100)
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )

    graph = export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )

    for fingerprint in replay.dependency_fingerprints:
        node = graph.node(
            dependency_fingerprint_node_id(
                fingerprint.dependency_kind,
                fingerprint.dependency_id,
            )
        )
        assert node is not None
        assert node.node_kind == "dependency_fingerprint"
        assert node.digest == fingerprint.fingerprint
        assert _has_edge(graph, graph.receipt_node_id, node.node_id, "pinned_dependency")


def test_graph_payload_hides_raw_committed_values_by_default():
    case = receipt_projection_case(amount=100, site="plant-a")
    artifacts = artifact_store_for_receipt(
        case.receipt,
        committed_values=case.source_values,
    )
    replay = replay_public_projection(
        case.source_values,
        case.projection,
        receipt=case.receipt,
        artifacts=artifacts,
    )

    graph = export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )
    payload = graph.to_payload()

    assert "plant-a" not in repr(payload)
    assert not _payload_has_key(payload, "value")
    assert not _payload_has_key(payload, "output_value")
    assert not _payload_has_key(payload, "text")


def test_graph_export_rejects_replay_for_different_receipt_scope():
    first = receipt_projection_case(amount=100)
    second_receipt = replace(first.receipt, draft_id="draft-2")
    artifacts = artifact_store_for_receipt(
        first.receipt,
        committed_values=first.source_values,
    )
    replay = replay_public_projection(
        first.source_values,
        first.projection,
        receipt=first.receipt,
        artifacts=artifacts,
    )

    try:
        export_receipt_proof_graph(
            receipt=second_receipt,
            replay=replay,
            artifacts=artifacts,
        )
    except ProofGraphExportError as exc:
        assert "receipt key" in str(exc)
    else:
        raise AssertionError("Expected replay scope mismatch to block graph export.")


def test_graph_export_does_not_import_authority_or_compiler_functions():
    import comp.explanation.receipt_graph as receipt_graph

    assert "replay_public_projection" not in receipt_graph.__dict__
    assert "project_public_row" not in receipt_graph.__dict__
    assert "CompilerTool" not in receipt_graph.__dict__


def _has_edge(
    graph: ReceiptProofGraph,
    source_id: str,
    target_id: str,
    edge_kind: str,
) -> bool:
    return bool(graph.edges_between(source_id, target_id, edge_kind=edge_kind))


def _payload_has_key(value, key: str) -> bool:
    if isinstance(value, dict):
        return key in value or any(_payload_has_key(item, key) for item in value.values())
    if isinstance(value, (tuple, list)):
        return any(_payload_has_key(item, key) for item in value)
    return False
