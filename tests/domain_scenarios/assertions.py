from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from comp import ProjectionBlocked, ProjectionSpec, project_public_row


def assert_projection_tamper_blocked(
    result,
    projection: ProjectionSpec,
    overrides: Mapping[str, Any],
    *,
    match: str = "value commitment",
) -> None:
    if result.projection is None:
        raise AssertionError("scenario result has no projection to tamper")
    if result.preparation.receipt is None:
        raise AssertionError("scenario result has no receipt to enforce projection")

    tampered_values = dict(result.projection)
    tampered_values.update(overrides)

    with pytest.raises(ProjectionBlocked, match=match):
        project_public_row(
            tampered_values,
            projection,
            receipt=result.preparation.receipt,
        )


def assert_receipt_trace(
    result,
    *,
    reference_binding_ids: tuple[str, ...] | None = None,
    derived_claim_ids: tuple[str, ...] | None = None,
    calculation_trace_ids: tuple[str, ...] | None = None,
    formula_ids: tuple[str, ...] | None = None,
) -> None:
    if result.preparation.receipt is None:
        raise AssertionError("scenario result has no receipt")
    if result.preparation.receipt.citations is None:
        raise AssertionError("scenario receipt has no citations")

    citations = result.preparation.receipt.citations
    if reference_binding_ids is not None:
        assert citations.reference_binding_ids == reference_binding_ids
    if derived_claim_ids is not None:
        assert citations.derived_claim_ids == derived_claim_ids
    if calculation_trace_ids is not None:
        assert citations.calculation_trace_ids == calculation_trace_ids
    if formula_ids is not None:
        assert citations.formula_ids == formula_ids


def assert_proof_graph_contract(
    result,
    *,
    required_fields: Sequence[str] = (),
    required_node_kinds: Sequence[str] = (),
    required_node_ids: Sequence[str] = (),
    required_edge_kinds: Sequence[str] = (),
) -> None:
    from tests.domain_scenarios.views import scenario_result_view

    graph = scenario_result_view(result).get("proof_graph")
    if graph is None:
        raise AssertionError("scenario result has no proof graph")

    assert graph["authority"] == "explanation_only"
    assert graph["can_authorize_public_projection"] is False
    assert not _payload_has_key(graph, "value")
    assert not _payload_has_key(graph, "text")

    nodes = tuple(graph["nodes"])
    edges = tuple(graph["edges"])
    node_ids = {node["node_id"] for node in nodes}
    node_kinds = {node["node_kind"] for node in nodes}
    edge_kinds = {edge["edge_kind"] for edge in edges}
    field_paths = {
        path["field"]: tuple(path["node_ids"])
        for path in graph["field_paths"]
    }

    for field in required_fields:
        if field not in field_paths:
            raise AssertionError(f"proof graph missing field path: {field}")
        path = field_paths[field]
        assert path[-1] == graph["receipt_node_id"]
        assert any(f":{field}" in node_id for node_id in path)

    for node_kind in required_node_kinds:
        if node_kind not in node_kinds:
            raise AssertionError(f"proof graph missing node kind: {node_kind}")

    for node_id in required_node_ids:
        if node_id not in node_ids:
            raise AssertionError(f"proof graph missing node id: {node_id}")

    for edge_kind in required_edge_kinds:
        if edge_kind not in edge_kinds:
            raise AssertionError(f"proof graph missing edge kind: {edge_kind}")

    for node in nodes:
        if node["node_kind"] == "dependency_fingerprint":
            assert _has_edge(
                edges,
                graph["receipt_node_id"],
                node["node_id"],
                "pinned_dependency",
            )


def assert_no_proof_graph(result) -> None:
    from tests.domain_scenarios.views import scenario_result_view

    assert scenario_result_view(result).get("proof_graph") is None


def _has_edge(
    edges: Sequence[Mapping[str, Any]],
    source_id: str,
    target_id: str,
    edge_kind: str,
) -> bool:
    return any(
        edge["source_id"] == source_id
        and edge["target_id"] == target_id
        and edge["edge_kind"] == edge_kind
        for edge in edges
    )


def _payload_has_key(value, key: str) -> bool:
    if isinstance(value, Mapping):
        return key in value or any(
            _payload_has_key(item, key)
            for item in value.values()
        )
    if isinstance(value, (tuple, list)):
        return any(_payload_has_key(item, key) for item in value)
    return False


__all__ = [
    "assert_no_proof_graph",
    "assert_proof_graph_contract",
    "assert_projection_tamper_blocked",
    "assert_receipt_trace",
]
