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

1. `architecture/authority-map.md`
2. `architecture/kill-list.md`
3. `architecture/obligation-kernel-working-theory.md`
4. `architecture/llm-orchestrated-compiler-tool-loop.md`
5. `architecture/memory-assisted-compiler-loop.md`

`architecture/obligation-kernel-working-theory.md` is the broad working map for
semantic obligations, reference-grounded calculation, commit packages,
governance decisions, and receipt-gated projection.

## Compiler Tool Layers

Use this layer map when adding code or reviewing PRs:

```text
semantic
  ProofObligation(kind="semantic_judgment_required")
  SemanticJudgment protocol validation

reference
  ReferenceCandidate
  ReferenceBinding
  deterministic reference selection

calculation
  CalculationRequirement
  CalculationTrace
  DerivedClaim

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
