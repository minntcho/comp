# Receipt Proof Graph Boundary Prework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare the receipt proof graph boundary so follow-up PRs can add CLI/JSON export, scenario attachment, and renderers without weakening the receipt/replay authority model.

**Architecture:** Keep `ReceiptProofGraph` in `comp.explanation` as the explanation IR derived from a successful replay. Define an `ArtifactStore` read protocol at the persistence boundary, reserve `comp.views.receipt_graph` for render-only consumers, and update the active contract so payload names and renderer ownership are explicit before feature work begins.

**Tech Stack:** Python dataclasses, typing `Protocol`, pytest, repository architecture docs.

---

### Task 1: Document Payload And Renderer Boundaries

**Files:**
- Modify: `docs/architecture/receipt-proof-graph.md`
- Test: `tests/test_package_smoke.py`

- [ ] **Step 1: Write the failing doc-boundary test**

Add a smoke test that requires the active contract to name the stable scenario key, renderer module, and MySQL boundary:

```python
def test_receipt_proof_graph_contract_names_prework_boundaries():
    graph_doc = Path("docs/architecture/receipt-proof-graph.md").read_text(
        encoding="utf-8"
    )

    assert "proof_graph" in graph_doc
    assert "dependency_graph" not in graph_doc
    assert "comp.views.receipt_graph" in graph_doc
    assert "MySQLArtifactStore is an ArtifactStore implementation" in graph_doc
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_package_smoke.py::test_receipt_proof_graph_contract_names_prework_boundaries -q
```

Expected: FAIL because the current document still mentions `dependency_graph` and does not reserve `comp.views.receipt_graph`.

- [ ] **Step 3: Update the active contract**

Modify `docs/architecture/receipt-proof-graph.md` so section 11 uses this shape:

```text
Scenario viewer payloads may expose the graph alongside existing traces:

receipt_trace      receipt citation summary
replay_trace       replay verification summary
proof_graph        receipt-scoped proof DAG

Use `proof_graph`, not `dependency_graph`, because the payload explains
receipt-gated proof paths rather than arbitrary dependency edges.

CLI, Mermaid, Graphviz, and UI rendering should consume the graph payload rather
than reconstructing graph semantics independently. Renderer code belongs in
`comp.views.receipt_graph` or downstream viewer packages; it must not call the
compiler, resolver, calculator, governance gate, projection gate, or replay
function.

`MySQLArtifactStore` is an `ArtifactStore` implementation. It stores and
retrieves replay artifacts; it does not become a graph backend or a policy
authority.
```

Update the recommended first slice so it says `scenario JSON includes proof_graph`.

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python -m pytest tests/test_package_smoke.py::test_receipt_proof_graph_contract_names_prework_boundaries -q
```

Expected: PASS.

### Task 2: Define The ArtifactStore Read Boundary

**Files:**
- Modify: `comp/persistence/ledger.py`
- Modify: `comp/persistence/__init__.py`
- Modify: `comp/explanation/receipt_graph.py`
- Test: `tests/test_receipt_proof_graph.py`
- Test: `tests/test_package_smoke.py`

- [ ] **Step 1: Write the failing type-boundary test**

Add imports:

```python
from typing import get_type_hints

import comp.explanation.receipt_graph as receipt_graph
from comp.persistence import ArtifactStore
```

Add the test:

```python
def test_graph_export_depends_on_artifact_store_protocol():
    hints = get_type_hints(receipt_graph.export_receipt_proof_graph)

    assert hints["artifacts"] is ArtifactStore
    assert getattr(ArtifactStore, "_is_protocol", False) is True
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_receipt_proof_graph.py::test_graph_export_depends_on_artifact_store_protocol -q
```

Expected: FAIL because `ArtifactStore` is not exported yet and the graph exporter is annotated with `InMemoryArtifactStore`.

- [ ] **Step 3: Add the protocol**

In `comp/persistence/ledger.py`, add:

```python
from typing import Protocol
```

Then add:

```python
class ArtifactStore(Protocol):
    def get(self, artifact_id: str) -> ArtifactEnvelope:
        ...
```

Export it in `__all__`.

- [ ] **Step 4: Export and consume the protocol**

In `comp/persistence/__init__.py`, import and export `ArtifactStore`.

In `comp/explanation/receipt_graph.py`, replace the `InMemoryArtifactStore` import and annotations with `ArtifactStore`.

- [ ] **Step 5: Add package smoke coverage**

In `test_pyproject_packages_comp_core_scenarios_and_agent_layer`, import `ArtifactStore` from `comp.persistence` and assert it is not `None`.

- [ ] **Step 6: Run the focused tests**

Run:

```bash
python -m pytest tests/test_receipt_proof_graph.py tests/test_package_smoke.py::test_pyproject_packages_comp_core_scenarios_and_agent_layer -q
```

Expected: PASS.

### Task 3: Reserve The Renderer Module Without Adding Renderers

**Files:**
- Create: `comp/views/receipt_graph.py`
- Modify: `comp/views/__init__.py`
- Test: `tests/test_package_smoke.py`

- [ ] **Step 1: Write the failing renderer-boundary test**

Add:

```python
def test_receipt_graph_renderers_have_non_authority_module_boundary():
    from comp.views import receipt_graph

    assert "render-only" in (receipt_graph.__doc__ or "")
    assert "export_receipt_proof_graph" not in receipt_graph.__dict__
    assert "replay_public_projection" not in receipt_graph.__dict__
    assert "project_public_row" not in receipt_graph.__dict__
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python -m pytest tests/test_package_smoke.py::test_receipt_graph_renderers_have_non_authority_module_boundary -q
```

Expected: FAIL because `comp.views.receipt_graph` does not exist yet.

- [ ] **Step 3: Add the reserved module**

Create `comp/views/receipt_graph.py`:

```python
"""Render-only receipt proof graph view helpers.

This module is reserved for Mermaid, Graphviz, and viewer formatters that
consume `ReceiptProofGraph.to_payload()`. It must not export graphs, replay
projections, or authorize public rows.
"""

__all__: list[str] = []
```

Update `comp/views/__init__.py` to expose only the module:

```python
"""Projection and explanation view helpers."""
```

- [ ] **Step 4: Run the focused test**

Run:

```bash
python -m pytest tests/test_package_smoke.py::test_receipt_graph_renderers_have_non_authority_module_boundary -q
```

Expected: PASS.

### Task 4: Verify The Boundary Prework

**Files:**
- No new files.

- [ ] **Step 1: Run focused graph and package tests**

Run:

```bash
python -m pytest tests/test_receipt_proof_graph.py tests/test_package_smoke.py -q
```

Expected: PASS.

- [ ] **Step 2: Check the diff**

Run:

```bash
git diff --check
git status --short
```

Expected: no whitespace errors; changed files are limited to docs, persistence typing, explanation annotations, views boundary, and tests.

- [ ] **Step 3: Commit the prework**

Run:

```bash
git add docs/architecture/receipt-proof-graph.md docs/superpowers/plans/2026-05-22-receipt-proof-graph-boundary-prework.md comp/persistence/ledger.py comp/persistence/__init__.py comp/explanation/receipt_graph.py comp/views/__init__.py comp/views/receipt_graph.py tests/test_package_smoke.py tests/test_receipt_proof_graph.py
git commit -m "chore: clarify receipt graph export boundaries"
```

Expected: one small prework commit ready for the first sequential PR.
