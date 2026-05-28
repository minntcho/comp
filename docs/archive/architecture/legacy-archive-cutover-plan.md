# Legacy Archive Cutover Plan

Status: historical-note
Owner: docs
Last checked against code: 2026-05-20
Can block PRs: no

Historical note. This document cannot block PRs and must not be cited as current guidance.

This document defines the PR sequence for moving `comp` from the legacy
pass-pipeline surface toward the authority-first compiler-tool architecture.

It is a planning document only. PR0 does not move code, change package exports,
or alter runtime behavior.

---

## 1. Target Architecture

The active architecture is:

```text
InterpretationHypothesis
-> CompilerTool
-> CompileReport / ProofObligations
-> Judgment Facts
-> Governance Decision
-> Receipt
-> Projection
```

The compiler tool is an obligation oracle. It checks a proposed interpretation
against deterministic contracts and returns structured diagnostics, unknowns,
unchecked areas, hazards, and proof obligations.

The public truth boundary is not the LLM and not a row. Public projection must
be gated by governance and receipt authority.

---

## 2. Active Surface

The active rebuild surface should keep:

```text
comp.judgment/*
docs/architecture/*
minimal package metadata needed to expose the active package
CompilerTool / CompileReport / ProofObligation models
focused judgment, compiler-tool, and receipt tests
```

`comp.judgment` remains the active kernel unless a later architecture document
explicitly supersedes it.

Useful active concepts include:

```text
Fact
JudgmentState
FixpointEngine
candidate frontier helpers
SelectionReceipt
CommitReceipt
```

---

## 3. Legacy And Archive Targets

The legacy pass pipeline may remain as reference material during the cutover,
but it must not define long-term authority.

Archive candidates include:

```text
CompileArtifacts
LexPass
ParsePass
ScopeResolutionPass
InferencePass
SemanticPass
RepairPass
EmitPass
GovernancePass
CalculationPass
pipeline_runner
compiled_pipeline_runner
comp.compat legacy wrappers
comp.pipeline legacy pass exports
row.status / merge_log / event_log centered tests
golden tests that assert legacy row pipeline behavior
```

The goal is not to hide history. The goal is to stop legacy transport from
being promoted into the new kernel.

---

## 4. Hard Constraints

Every cutover PR must preserve these constraints:

```text
Unchecked is not pass.
CompileReport is not receipt.
Legacy parity is not success.
```

More explicitly:

```text
Do not promote CompileArtifacts to kernel state.
Do not treat row.status as commit truth.
Do not make GovernancePass a long-term authority boundary.
Do not treat legacy/package parity as architecture success.
Do not create public projection without receipt authority.
Do not treat CompileReport acceptance as public projection authority.
```

---

## 5. Terminology

`UnknownClaim` means the compiler has a known rule or validation family, but
cannot decide because evidence or context is missing.

Example:

```text
period=Jan exists, but reporting_year is missing.
```

`UncheckedArea` means the compiler lacks an active rule family for the semantic
area.

Example:

```text
factor_period_compatibility has no active rule.
```

Rules:

```text
UncheckedArea must never count as pass.
UnknownClaim must not become failure unless a rule says missing context blocks.
UncheckedArea should produce a rule-coverage obligation or review path.
```

---

## 6. PR Sequence

### PR0: Cutover Plan Document

Scope:

```text
Add docs/architecture/legacy-archive-cutover-plan.md.
```

Non-goals:

```text
No code changes.
No README edits.
No architecture policy edits.
No package export changes.
No legacy file moves or copies.
No test migration.
No CompilerTool implementation.
```

Reason:

```text
Fix the sequence and review boundaries before changing behavior.
```

### PR1: Active Surface Cut

Scope:

```text
Narrow top-level comp exports away from legacy runner facade.
Expose judgment-core symbols as the active top-level surface.
Document the active package surface.
Update package smoke tests.
```

Preflight:

```text
If PR #108 is open, treat it as PR1-in-progress.
Do not create a duplicate PR1.
```

Non-goals:

```text
No legacy file deletion.
No legacy archive move.
No pyproject py-modules cleanup.
No GovernancePass or row.status changes.
No CompilerTool implementation.
No LLM API integration.
```

### PR2: Legacy Archive Declaration

Scope:

```text
Document the legacy archive boundary.
Declare archived modules and tests.
Explain why the legacy pipeline is reference material, not active authority.
```

Non-goals:

```text
No legacy file moves.
No active package cleanup.
No behavioral refactor.
No CompilerTool implementation.
```

### PR3: Copy Legacy Pipeline Into Archive

Scope:

```text
Copy legacy pipeline modules into a temporary archive snapshot.
Copy legacy-oriented tests as reference material.
Keep original active files temporarily.
Document the archive copy boundary.
```

Current state:

```text
The temporary in-repository archive snapshot has been removed.
Use repository history when old pass-pipeline source text is needed.
```

Historical archive test policy:

```text
During the temporary archive phase, archived tests were not collected by active
pytest runs.
Do not let old row-pipeline tests define the active pass/fail status of the
rebuild branch.
```

Non-goals:

```text
No active file deletion.
No pyproject cleanup.
No package export changes beyond documentation needed for the archive.
No behavior changes.
```

### PR4: Remove Legacy From Active Packaging

Scope:

```text
Remove or shrink pyproject top-level py-modules.
Remove or archive comp.compat and comp.pipeline wrappers if they only preserve
legacy parity.
Move or mark legacy golden/e2e tests as archived reference tests.
Limit active tests to judgment, compiler-tool, and receipt behavior.
```

Split rule:

```text
If this becomes too large, split it into PR4a, PR4b, and PR4c rather than
mixing packaging cleanup, wrapper cleanup, and test migration in one diff.
```

Non-goals:

```text
No CompilerTool behavior beyond keeping active tests importable.
No public projection implementation.
No real LLM calls.
```

### PR5: CompilerTool Contract Slice

Scope:

```text
Add deterministic compiler-tool contract models.
Add a minimal CompilerTool vertical slice.
```

Minimum model set:

```text
InterpretationHypothesis
ClaimHypothesis
EvidenceWitness
CompileReport
CheckedClaim
FailedClaim
UnknownClaim
UncheckedArea
ProofObligation
Hazard
```

Required behavior:

```text
unsupported unit claim
-> blocked CompileReport
-> FailedClaim(field="unit")
-> ProofObligation(kind="find_source_witness")

revised hypothesis with missing unit hazard
-> review_required CompileReport
-> can_project_public_row == false
```

Constraints:

```text
Do not call real LLM providers.
Represent LLM proposals with deterministic InterpretationHypothesis fixtures.
Do not create public projection.
```

### PR6: CompileReport To Judgment Facts

Scope:

```text
Add an adapter from CompileReport into comp.judgment Fact records.
Use append-only facts.
Use FixpointEngine where useful.
```

Expected mappings:

```text
CheckedClaim -> Fact(tag="evidence")
FailedClaim -> Fact(tag="hazard_open")
UnknownClaim -> Fact(tag="hazard_open")
UncheckedArea -> Fact(tag="hazard_open")
ProofObligation -> Fact(tag="hazard_open")
resolved obligation -> Fact(tag="hazard_discharge")
```

Non-goals:

```text
No projection.
No legacy CompileArtifacts adapter unless explicitly scoped.
No real LLM calls.
```

### PR7: Receipt-Gated Projection

Scope:

```text
Add receipt-gated projection.
Require CommitReceipt or equivalent governance/receipt authority before public
projection.
```

Required behavior:

```text
CompileReport accepted without CommitReceipt -> projection blocked
CommitReceipt present with committed field values -> projection allowed
```

Non-goals:

```text
No restoration of row.status as truth.
No merge_log as receipt substitute.
No legacy GovernancePass authority boundary.
```

---

## 7. Concurrent PR Policy

Before starting each PR, inspect open PRs.

Known concurrent PR handling:

```text
If PR #108 is open, treat it as PR1-in-progress and do not duplicate it.
If PR #106 is open, keep Lark frontend content out of PR0-PR7 unless it is
explicitly merged, updated, or superseded.
Avoid editing the same README or architecture policy sections across concurrent PRs
unless the PR explicitly reconciles them.
```

---

## 8. Test Policy

Docs-only PRs should verify the intended diff and may skip runtime tests if no
code changed.

Code PRs should use focused tests first, then broader tests where available.

If project test dependencies are missing, report the exact blocker and do not
claim tests pass.

After the cutover, active test status should come from:

```text
judgment tests
compiler-tool contract tests
CompileReport-to-Fact adapter tests
receipt-gated projection tests
```

Archived tests are reference material. They must not define active pass/fail
status.

---

## 9. Completion Criteria

The cutover is complete when:

```text
Top-level comp no longer represents the legacy runner facade.
Legacy pass-pipeline modules are archived or outside active packaging.
Active package tests no longer depend on row.status or merge_log as truth.
CompilerTool returns structured reports with obligations, unknowns, and
unchecked areas.
CompileReport output can be translated into append-only judgment facts.
Public projection is impossible without receipt authority.
```
