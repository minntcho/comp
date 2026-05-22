from comp.explanation import export_receipt_proof_graph
from comp.persistence import replay_public_projection
from comp.views.receipt_graph import render_graphviz_dot, render_mermaid
from tests.support.persistence_cases import (
    artifact_store_for_receipt,
    receipt_projection_case,
)


def test_receipt_graph_view_renders_mermaid_without_raw_values():
    graph = _sample_graph()

    output = render_mermaid(graph.to_payload())

    assert output.startswith("flowchart TD\n")
    assert "commit_receipt" in output
    assert "public_projection" in output
    assert "-- \"authorized_by\" -->" in output
    assert "plant-a" not in output
    assert "value" not in output
    assert graph.receipt_node_id not in output


def test_receipt_graph_view_renders_graphviz_dot_without_raw_values():
    graph = _sample_graph()

    output = render_graphviz_dot(graph.to_payload())

    assert output.startswith("digraph ReceiptProofGraph {\n")
    assert "rankdir=LR;" in output
    assert "commit_receipt" in output
    assert "public_projection" in output
    assert "[label=\"authorized_by\"]" in output
    assert "plant-a" not in output
    assert "value" not in output


def _sample_graph():
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
    return export_receipt_proof_graph(
        receipt=case.receipt,
        replay=replay,
        artifacts=artifacts,
    )
