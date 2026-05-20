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

Read these first:

1. `architecture/trust-kernel-extension-rings.md`
2. `architecture/retrieval-fabric-north-star.md`
3. `architecture/obligation-kernel-working-theory.md`
4. `architecture/trust-kernel-hardening.md`
5. `architecture/domain-scenario-pack-generation.md`
6. `architecture/llm-orchestrated-compiler-tool-loop.md`
7. `architecture/llm-worker-orchestration.md`
8. `architecture/memory-assisted-compiler-loop.md`

`architecture/trust-kernel-extension-rings.md` is the active architecture frame
for keeping `comp` small: outer rings submit artifacts or render views, while
only deterministic gates inside the trust kernel promote authority.

`architecture/retrieval-fabric-north-star.md` is the long-term direction for
retrieval, embedding, LLM artifact resolution, typed reference authority, and
compiler/receipt gates.

`architecture/obligation-kernel-working-theory.md` is the detailed working map
for current implementation slices: semantic obligations, reference-grounded
calculation, commit packages, governance decisions, and receipt-gated
projection.

`architecture/trust-kernel-hardening.md` is the implementation standard for the
next hardening slice: remove ambient domain defaults, fingerprint profile-active
behavior, preserve retrieval/reference provenance, and make the canonical
scenario persistence-replayable.

`architecture/domain-scenario-pack-generation.md` describes how to add
replaceable Domain Scenario Lab packs without turning them into hard-coded
golden fixtures.

`architecture/llm-worker-orchestration.md` records a provisional background LLM
worker hypothesis: work orders, allowed tool menus, typed artifact submission,
abstention, and scoreless embedding-informed routing.

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
