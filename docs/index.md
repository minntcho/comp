# docs

This directory tracks the active architecture for the `comp` rebuild.

## Current Architecture

`comp` is now a receipt-gated proof package compiler:

```text
candidate / obligation / judgment / reference / calculation
-> ReviewPackage
-> ReviewDecision
-> PublicOutputReceipt
-> Judgment Facts
-> receipt-gated projection
```

The compiler does not create public truth directly. Public projection requires a
`PublicOutputReceipt`.

## Active Map

Read `architecture/document-governance.md` first when deciding whether a
document can block a PR. The rest of the architecture docs are grouped by that
authority model.

The document header is the metadata source of truth for `Status`, `Owner`,
`Last checked against code`, and `Can block PRs`. For finding governed docs,
this index is the navigation source of truth.

### Active Contracts

These documents can block PRs when a change violates their authority boundary
without explicitly updating the contract.

1. `architecture/document-governance.md`
2. `architecture/contracts/trust-kernel-extension-rings.md`
3. `architecture/contracts/policy-boundary.md`
4. `architecture/contracts/compiler-domain-boundary.md`
5. `architecture/contracts/extension-port-contracts.md`
6. `architecture/contracts/artifact-envelope-builder.md`
7. `architecture/contracts/persistence-ledger-boundary.md`
8. `architecture/contracts/receipt-proof-graph.md`
9. `architecture/contracts/trust-kernel-hardening.md`
10. `architecture/contracts/memory-assisted-compiler-loop.md`
11. `architecture/contracts/friendly-authority-vocabulary.md`

### Implementation Maps

These documents track the current implementation shape. They can block a PR
when the PR changes the mapped area but leaves the map stale.

1. `architecture/maps/obligation-kernel-working-theory.md`
2. `architecture/maps/domain-scenario-pack-generation.md`
3. `architecture/maps/internal-execution-design-map.md`
4. `architecture/maps/policy-assembled-trust-kernel.md`

### North Stars

These documents guide roadmap direction and review questions. They do not
override active contracts.

1. `architecture/north-stars/retrieval-fabric-north-star.md`
2. `architecture/north-stars/llm-worker-orchestration.md`
3. `architecture/north-stars/production-trust-spine-database.md`
4. `architecture/north-stars/scenario-trust-runtime-bridge.md`

### Historical Notes

These documents preserve migration context and older reasoning. They cannot
block PRs by themselves.

1. `archive/architecture/active-surface-cutover.md`
2. `archive/architecture/legacy-archive-cutover-plan.md`
3. `archive/architecture/llm-orchestrated-compiler-tool-loop.md`

## API References

These documents classify public package surfaces. They are not architecture
authority contracts unless an active contract explicitly references them.

1. `api/compiler-tool.md`
2. `api/public-output-gate.md`
3. `api/scenario-contracts.md`

## Examples

Examples are runnable or copyable guides for public surfaces. They are not
authority contracts unless an active contract explicitly references them.

1. `examples/scenario_contracts/README.md`
2. `examples/scenario_pack_repo/README.md`

## Compiler Tool Layers

Use this layer map when adding code or reviewing PRs:

```text
semantic
  ValidationRequirement(kind="semantic_judgment_required")
  SemanticJudgment protocol validation

reference
  ReferenceQuery
  ReferenceResolver / EmbeddingResolverStub
  reference_search_required -> candidate-only ReferenceOption
  ReferenceOption
  CanonicalReference
  deterministic reference selection

calculation
  CalculationRequirement
  CalculationTrace
  CalculatedClaim

resolver tasks
  ValidationRequirement -> ResolverTask
  RetrievalQueryPolicy
  ResolverTask -> ReferenceQuery
  resolver-facing task type, required artifact, and payload

governance / commit
  ReviewPackage
  ReviewDecision
  PublicOutputReceipt builder
  CommitPreparation

judgment facts
  ValidationReport -> Fact
  CommitPreparation -> Fact
```

Extractor work, including Lark, belongs before the compiler tool. Extractors
produce evidence and claim hypotheses; they do not authorize projection.

Agent work, including `minchoagnt`, belongs outside the compiler core. Agents may
consume `ResolverTask` items and submit resolver artifacts such as semantic
judgments or reference queries, but they do not mint commit receipts.

## Historical Reference

Later migration documents and legacy pass-pipeline snapshots are preserved in
repository history, not as active tree content. Archive notes live at:

```text
docs/archive/2026-migration/README.md
```

Historical migration documents are reference material, not active policy for
this branch.

Implementation plans and execution logs are archived under:

```text
docs/archive/plans/
```
