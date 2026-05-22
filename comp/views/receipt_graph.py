"""Render-only receipt proof graph view helpers.

This module is reserved for Mermaid, Graphviz, and viewer formatters that
consume `ReceiptProofGraph.to_payload()`. It must not export graphs, replay
projections, or authorize public rows.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


def render_mermaid(graph_payload: Mapping[str, Any]) -> str:
    """Render a receipt proof graph payload as Mermaid flowchart text."""

    aliases: dict[str, str] = {}
    lines = ["flowchart TD"]
    for node in _nodes(graph_payload):
        node_id = _required_text(node, "node_id")
        alias = _alias_for(node_id, aliases)
        label = _node_label(node)
        lines.append(f'  {alias}["{_mermaid_text(label)}"]')
    for edge in _edges(graph_payload):
        source_alias = _alias_for(_required_text(edge, "source_id"), aliases)
        target_alias = _alias_for(_required_text(edge, "target_id"), aliases)
        edge_kind = _required_text(edge, "edge_kind")
        lines.append(
            f'  {source_alias} -- "{_mermaid_text(edge_kind)}" --> {target_alias}'
        )
    return "\n".join(lines) + "\n"


def render_graphviz_dot(graph_payload: Mapping[str, Any]) -> str:
    """Render a receipt proof graph payload as Graphviz DOT text."""

    aliases: dict[str, str] = {}
    lines = ["digraph ReceiptProofGraph {", "  rankdir=LR;"]
    for node in _nodes(graph_payload):
        node_id = _required_text(node, "node_id")
        alias = _alias_for(node_id, aliases)
        label = _node_label(node)
        lines.append(f'  {alias} [label="{_dot_text(label)}"];')
    for edge in _edges(graph_payload):
        source_alias = _alias_for(_required_text(edge, "source_id"), aliases)
        target_alias = _alias_for(_required_text(edge, "target_id"), aliases)
        edge_kind = _required_text(edge, "edge_kind")
        lines.append(
            f'  {source_alias} -> {target_alias} [label="{_dot_text(edge_kind)}"];'
        )
    lines.append("}")
    return "\n".join(lines) + "\n"


def _nodes(graph_payload: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    return _mapping_sequence(graph_payload.get("nodes", ()), "nodes")


def _edges(graph_payload: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    return _mapping_sequence(graph_payload.get("edges", ()), "edges")


def _mapping_sequence(value: Any, name: str) -> Sequence[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError(f"Expected array for {name}.")
    for item in value:
        if not isinstance(item, Mapping):
            raise TypeError(f"Expected object items for {name}.")
    return value


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise TypeError(f"Expected non-empty string for {key}.")
    return value


def _alias_for(node_id: str, aliases: dict[str, str]) -> str:
    alias = aliases.get(node_id)
    if alias is None:
        alias = f"n{len(aliases)}"
        aliases[node_id] = alias
    return alias


def _node_label(node: Mapping[str, Any]) -> str:
    return f"{_required_text(node, 'node_kind')}: {_required_text(node, 'label')}"


def _mermaid_text(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;").replace("\n", "<br/>")


def _dot_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


__all__ = ["render_graphviz_dot", "render_mermaid"]
