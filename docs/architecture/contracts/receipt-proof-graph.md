# Receipt Proof Graph

Status: active-contract
Owner: explanation
Last checked against code: 2026-05-22
Can block PRs: yes

This document fixes the role of receipt-scoped graph export in the active
`comp` rebuild. The graph is not a trust-kernel feature, a compiler decision,
or a replacement for receipt replay. It is an explanation-only read model that
normalizes a successful replay into a graph-friendly form.

The short version:

```text
Receipt authorizes.
Replay verifies.
Graph explains.
UI renders.
```

## 1. Core Decision

`comp` should stay graphable, but it should not make a graph engine part of the
trust kernel.

The receipt proof graph belongs outside the authority path:

```text
PublicOutputReceipt
-> ProjectionReplayReport
-> ReceiptProofGraph
-> Viewer / CLI / UI / Mermaid / Graphviz
```

The forbidden inverse is:

```text
ReceiptProofGraph
-> projection validity
```

Graph export success must never imply that a public projection is valid. Validity
comes from a clean `PublicOutputReceipt` and successful `replay_public_projection(...)`.

## 2. Layer Placement

The graph layer is an explanation layer:

```text
Trust Kernel
  CheckedClaim
  CanonicalReference
  CalculatedClaim
  ReviewPackage
  ReviewDecision
  PublicOutputReceipt

Persistence / Replay
  ArtifactEnvelope
  ReceiptLedger
  replay_public_projection(...)
  ProjectionReplayReport

Explanation / Graph
  ReceiptProofGraph
  graph node / edge export
  field-level proof paths

Product / Viewer
  CLI summaries
  JSON viewer payloads
  Mermaid / Graphviz / UI rendering
```

The import direction should be one-way:

```text
comp.explanation may import comp.persistence and comp.judgment.
comp.persistence must not import comp.explanation.
comp.compiler_tool must not import comp.explanation.
receipt builders must not import comp.explanation.
```

This keeps graph behavior from becoming authority behavior by accident.

## 3. Explanation IR, Not Visualization

`ReceiptProofGraph` is a product-language concept, not just a diagram feature.
It answers a human question:

```text
Why is this public value allowed to exist?
```

It should make the receipt path inspectable:

```text
source evidence
-> evidence witness
-> checked claim
-> reference binding
-> calculation trace
-> derived claim
-> commit package
-> governance decision
-> commit receipt
-> public projection
```

The UI may render the graph, but the graph is the intermediate explanation IR.
The UI is only a renderer.

## 4. Graphability Invariant

The system should preserve enough structure that important artifacts can become
graph nodes and important dependencies can become graph edges later.

This does not require a large graph system now. It does require these invariants:

```text
EvidenceRef keeps stable id, source/span/text, and fingerprint material.
CheckedClaim keeps its witness id.
CanonicalReference keeps selected reference id and rejection context.
CalculatedClaim keeps its CalculationTrace.
CalculationTrace keeps formula and input/source references.
PublicOutputReceipt keeps projection, value, and dependency citations.
ProjectionReplayReport keeps artifact refs, digests, and dependency fingerprints.
```

If graph export cannot connect these artifacts, that is evidence of a provenance
gap in the system design.

## 5. V0 Scope

The first implementation slice should stay receipt-scoped:

```text
PublicOutputReceipt
ProjectionReplayReport
ArtifactStore
-> ReceiptProofGraph
```

Allowed behavior:

```text
create nodes
create edges
attach artifact kind
attach digest metadata
attach field names and source ids
expose field-level proof paths
```

Forbidden behavior:

```text
minting PublicOutputReceipt
creating ReviewDecision
authorizing projection
selecting claims
binding references
recomputing calculations
walking the entire ValidationReport
walking all ResolverTask items
including full retrieval candidate frontiers
including LLM work-order histories
exposing raw committed values by default
```

The graph should be built only after replay has succeeded.

## 6. API Shape

The preferred package location is:

```text
comp/explanation/receipt_graph.py
```

The graph exporter should be read-only:

```python
def export_receipt_proof_graph(
    *,
    receipt: PublicOutputReceipt,
    replay: ProjectionReplayReport,
    artifacts: ArtifactStore,
) -> ReceiptProofGraph:
    ...
```

The exporter may inspect receipt citations, replay artifact refs, replay
dependency fingerprints, and stored artifact envelopes. It should not call the
compiler, resolver, selector, calculator, governance gate, or projection gate.

The graph model should carry an explicit non-authority marker:

```python
ReceiptProofGraph(
    nodes=(...),
    edges=(...),
    authority="explanation_only",
    can_authorize_public_projection=False,
)
```

## 7. Node And Edge Shape

V0 nodes should be simple and stable:

```python
GraphNode(
    node_id: str,
    node_kind: str,
    label: str,
    digest: str | None,
    metadata: Mapping[str, object],
)
```

Initial node kinds:

```text
public_projection
public_field
commit_receipt
governance_decision
commit_package
derived_claim
calculation_trace
checked_claim
evidence_witness
reference_binding
reference_record
reference_catalog_snapshot
compiler_profile
domain_pack
rule_family
semantic_rubric
calculation_formula
dependency_fingerprint
```

V0 edges should explain support direction from source/supporting artifact toward
the artifact it supports:

```python
GraphEdge(
    source_id: str,
    target_id: str,
    edge_kind: str,
    metadata: Mapping[str, object],
)
```

Initial edge kinds:

```text
grounded_by
checked_from
selected_reference
covered_by_snapshot
calculated_with
derived_from
committed_in
decided_by
authorized_by
projected_as
pinned_dependency
uses_profile
uses_domain_pack
uses_formula
```

The exact node and edge set may evolve, but it should remain derived from
receipt/replay artifacts in V0.

## 8. Raw Value Policy

Graph payloads should not expose raw committed values by default.

Prefer field names, artifact ids, source kinds, and digests:

```json
{
  "node_id": "checked_claim:electricity_kwh:w-electricity-kwh",
  "node_kind": "checked_claim",
  "label": "Checked claim: electricity_kwh",
  "digest": "sha256:...",
  "metadata": {
    "field": "electricity_kwh",
    "has_value_commitment": true
  }
}
```

If a product later needs to show values, that should be a separate viewer policy,
not the default graph export contract.

## 9. Field-Level Proof Paths

The full graph is useful, but product workflows usually begin at a field:

```text
public_row.co2e_kg
```

The graph layer supports a read-only field explanation helper:

```python
explain_public_field(graph, field="co2e_kg")
```

The helper returns a `PublicFieldExplanation` path through existing graph nodes
only. It should not search the full compile report, call
`replay_public_projection(...)`, call the projection gate, inspect an
`ArtifactStore`, or infer missing provenance.

The return model is explicitly explanation-only:

```python
PublicFieldExplanation(
    field="co2e_kg",
    field_node_id="public_field:...",
    authorized_by="commit_receipt:...",
    path_node_ids=(...),
    authority="explanation_only",
    can_authorize_public_projection=False,
)
```

Unknown fields, missing field paths, or paths that reference nodes outside
`graph.nodes` must fail clearly instead of inventing an explanation.

## 10. Completeness Tests

Graph tests should focus on authority boundaries and provenance completeness:

```text
every replay artifact ref appears as a node
every dependency fingerprint appears as a typed node
every public projection field connects to the PublicOutputReceipt
field-level explanations return existing field paths only
every cited checked claim connects to at least one evidence witness
every derived claim connects to calculation trace, formula, and dependencies
raw committed values are absent from graph payloads by default
graph.can_authorize_public_projection is false
graph export does not call projection authorization
tampered artifact replay blocks before graph export succeeds
graph nodes are not invented from outside receipt/replay scope in V0
```

The tests should not assert a large golden JSON blob. They should assert the
contract that graph export explains receipt-scoped authority without becoming
authority itself.

## 11. Product Surface

Scenario viewer payloads may expose the graph alongside existing traces:

```text
receipt_trace      receipt citation summary
replay_trace       replay verification summary
proof_graph        receipt-scoped proof DAG
```

Use `proof_graph`, not a generic dependency-graph name, because the payload
explains receipt-gated proof paths rather than arbitrary dependency edges.

CLI, Mermaid, Graphviz, and UI rendering should consume the graph payload rather
than reconstructing graph semantics independently. Renderer code belongs in
`comp.views.receipt_graph` or downstream viewer packages; it must not call the
compiler, resolver, calculator, governance gate, projection gate, or replay
function.

The CLI is file-based and exports a graph from an already materialized receipt,
replay report, and artifact envelope set. JSON remains the stable payload; the
Mermaid and Graphviz outputs are render-only views derived from that same graph:

```text
comp-receipt-graph export-json \
  --receipt receipt.json \
  --replay replay.json \
  --artifacts artifacts.json \
  --output proof-graph.json

comp-receipt-graph export-mermaid \
  --receipt receipt.json \
  --replay replay.json \
  --artifacts artifacts.json \
  --output proof-graph.mmd

comp-receipt-graph export-dot \
  --receipt receipt.json \
  --replay replay.json \
  --artifacts artifacts.json \
  --output proof-graph.dot
```

Existing graph payloads can also be rendered directly. This is the path for a
scenario JSON export that already contains `proof_graph`:

```text
python -m tests.domain_scenarios run synthetic_pcf.smoke.v1 \
  --json > scenario.json

comp-receipt-graph render-mermaid \
  --graph scenario.json \
  --output proof-graph.mmd

comp-receipt-graph render-dot \
  --graph proof-graph.json \
  --output proof-graph.dot
```

The CLI consumes replay outputs; it does not replay projections itself.
Artifact envelope bodies should use the persistence JSON codec so tuple, list,
decimal, and scalar values keep the same digest material they had at replay
time. Diagram renderers omit raw values and metadata by default; they are for
inspection, not for policy or projection decisions.

MySQLArtifactStore is an ArtifactStore implementation. It stores and
retrieves replay artifacts; it does not become a graph backend or a policy
authority.

The durable-path check is:

```text
MySQLReceiptLedger.get(...)
-> replay_public_projection(..., artifacts=MySQLArtifactStore)
-> export_receipt_proof_graph(..., artifacts=MySQLArtifactStore)
-> JSON / Mermaid / Graphviz renderer
```

This confirms MySQL can supply replay and graph-export inputs without moving
replay, explanation, or rendering authority into the database layer.

## 12. Deferred Graphs

Candidate and review graphs are important, but they are not V0.

Possible future rings:

```text
ReceiptProofGraph
  receipt-cited proof path only

CandidateFrontierGraph
  rejected candidates, near misses, resolver tasks, obligations

ReviewGraph
  human review, LLM abstention, conflict flags

ProductAuditGraph
  field-level proof, candidate frontier, and review history
```

These should only be added after the receipt-scoped graph is stable and still
clearly explanation-only.

## 13. Recommended First Slice

Recommended PR title:

```text
feat: export receipt proof graph
```

Candidate files:

```text
comp/explanation/__init__.py
comp/explanation/receipt_graph.py
tests/test_receipt_proof_graph.py
tests/domain_scenarios/views.py
```

Minimum behavior:

```text
successful replay can be normalized into ReceiptProofGraph
receipt-cited artifacts appear as nodes
dependency fingerprints appear as typed nodes
public projection and public fields connect back to the receipt
explain_public_field returns existing field paths without replaying
graph payload hides raw values by default
graph explicitly cannot authorize public projection
scenario JSON includes proof_graph
```

Non-goals:

```text
no graph database
no ORM
no production viewer
no interactive UI
no candidate frontier graph
no LLM reasoning graph
no retrieval score graph
no full event sourcing
no durable storage backend
```
