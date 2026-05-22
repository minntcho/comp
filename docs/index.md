# docs

This directory tracks the active architecture for the `comp` rebuild.

## Current Architecture

`comp` is now a receipt-gated proof package compiler:

```text
candidate / obligation / judgment / reference / calculation
-> CommitPackage
-> GovernanceDecision
-> CommitReceipt
-> Judgment Facts
-> receipt-gated projection
```

The compiler does not create public truth directly. Public projection requires a
`CommitReceipt`.

## Active Map

Read `architecture/document-governance.md` first when deciding whether a
document can block a PR. The rest of the architecture docs are grouped by that
authority model.

### Active Contracts

These documents can block PRs when a change violates their authority boundary
without explicitly updating the contract.

1. `architecture/document-governance.md`
2. `architecture/trust-kernel-extension-rings.md`
3. `architecture/extension-port-contracts.md`
4. `architecture/artifact-envelope-builder.md`
5. `architecture/persistence-ledger-boundary.md`
6. `architecture/receipt-proof-graph.md`
7. `architecture/trust-kernel-hardening.md`
8. `architecture/memory-assisted-compiler-loop.md`

### Implementation Maps

These documents track the current implementation shape. They can block a PR
when the PR changes the mapped area but leaves the map stale.

1. `architecture/obligation-kernel-working-theory.md`
2. `architecture/domain-scenario-pack-generation.md`

### North Stars

These documents guide roadmap direction and review questions. They do not
override active contracts.

1. `architecture/retrieval-fabric-north-star.md`
2. `architecture/llm-worker-orchestration.md`
3. `architecture/production-trust-spine-database.md`
4. `architecture/friendly-authority-vocabulary.md`
5. `architecture/scenario-trust-runtime-bridge.md`

### Historical Notes

These documents preserve migration context and older reasoning. They cannot
block PRs by themselves.

1. `architecture/active-surface-cutover.md`
2. `architecture/legacy-archive-cutover-plan.md`
3. `architecture/llm-orchestrated-compiler-tool-loop.md`

## Compiler Tool Layers

Use this layer map when adding code or reviewing PRs:

```text
semantic
  ProofObligation(kind="semantic_judgment_required")
  SemanticJudgment protocol validation

reference
  ReferenceQuery
  ReferenceResolver / EmbeddingResolverStub
  reference_search_required -> candidate-only ReferenceCandidate
  ReferenceCandidate
  ReferenceBinding
  deterministic reference selection

calculation
  CalculationRequirement
  CalculationTrace
  DerivedClaim

resolver tasks
  ProofObligation -> ResolverTask
  RetrievalQueryPolicy
  ResolverTask -> ReferenceQuery
  resolver-facing task type, required artifact, and payload

governance / commit
  CommitPackage
  GovernanceDecision
  CommitReceipt builder
  CommitPreparation

judgment facts
  CompileReport -> Fact
  CommitPreparation -> Fact
```

Extractor work, including Lark, belongs before the compiler tool. Extractors
produce evidence and claim hypotheses; they do not authorize projection.

Agent work, including `minchoagnt`, belongs outside the compiler core. Agents may
consume `ResolverTask` items and submit resolver artifacts such as semantic
judgments or reference queries, but they do not mint commit receipts.

## Historical Reference

Later migration documents are preserved outside the active surface at:

```text
legacy/current-migration-state-20260429
```

Archive notes live at:

```text
docs/archive/2026-migration/README.md
```

Historical migration documents are reference material, not active policy for
this branch.
