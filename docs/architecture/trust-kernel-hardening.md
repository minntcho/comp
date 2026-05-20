# Trust Kernel Hardening Standard

Status: active standard for the next hardening PRs.

This document fixes the implementation standard for the next slice of the
`comp` rebuild. The goal is to keep `comp` as a small trust kernel rather than
letting it drift back into an ESG row generator.

## Thesis

`comp` does not create truth. It compiles the conditions under which a value can
be claimed, records how those conditions were satisfied, and gates public
projection through a receipt.

The competitive surface is therefore not extraction accuracy. It is the ability
to contain LLM, embedding, and resolver output inside a deterministic authority
chain:

```text
candidate / resolver artifact
-> deterministic gate
-> canonical binding or open obligation
-> calculation trace
-> commit package
-> governance decision
-> commit receipt
-> receipt-gated projection
```

## Non-Negotiable Invariants

These invariants must remain true after every change:

```text
ReferenceCandidate != ReferenceBinding
Retrieval score != truth score
Embedding top-1 != selected reference
LLM worker output != public authority
DerivedClaim != public output
CompileReport != public authority
GovernanceDecision != public authority
CommitReceipt == public projection authority
```

Accepted reports, commit packages, and governance decisions may explain why a
projection is close to publishable. They must not authorize projection without a
clean `CommitReceipt`.

## Core / Domain Boundary

Core code must own protocol, not ESG meaning.

Core may know about:

```text
claims
witnesses
obligations
hazards
semantic judgments
reference candidates
reference bindings
derived claims
commit packages
governance decisions
commit receipts
projection gates
```

Domain packs, profiles, fixtures, or external reference resources must own:

```text
kWh
activity
amount
reporting_year
Scope 2
PCF
emission factor compatibility
domain-specific rule and rubric activation
projection field sets
```

The current `CompilerTool` ESG-ish defaults are acceptable only as a rebuild
artifact. The next implementation slice should make domain behavior explicit at
construction time or through profile/domain-pack fixtures.

## Profile Locking

A receipt should cite more than `profile_id`. It should preserve enough behavior
identity to explain the authority universe that produced the projection.

The minimum behavior fingerprint should include:

```text
profile_id
core_invariant_version
domain pack ids and versions
active rule ids
active rubric ids
judge policy id
active retrieval policy ids
projection policy id
```

The fingerprint must be canonical and deterministic. Changing any active
behavior input should change the fingerprint digest.

## Retrieval And Reference Provenance

Retrieval metadata is audit context, not authority. It should still be preserved
when it affects the route to a receipt.

Reference and retrieval traces should retain:

```text
reference DB version
retrieval index version
embedding model id when present
retrieval method
retrieval lens
selected candidate id
rejected candidate ids and reasons
canonical reference binding id
```

The first implementation should keep this small. It is enough for the canonical
scenario receipt or replay report to expose the relevant profile and retrieval
fingerprints. A full candidate graph can wait.

## Canonical Trace Product

The canonical scenario should become the representative trace product for the
project. It should show this full loop:

```text
raw evidence
-> deterministic extractor fixture
-> CompileReport obligations
-> retrieval candidates
-> deterministic ReferenceBinding
-> CalculationTrace / DerivedClaim
-> CommitPackage
-> GovernanceDecision
-> CommitReceipt
-> project_public_row
-> persistence replay
```

The scenario result should remain testable by targeted assertions, not by one
large golden JSON blob.

## Non-Goals

Do not add these in the hardening slice:

```text
real LLM provider calls
real vector DB
large ESG reference ingestion
quality score scalar
namespace-wide package relocation
general candidate graph
durable production ledger
```

The first durable ledger can be SQLite later. Before that, the receipt and
replay payloads must know what behavior and reference universe they are
recording.

## Review Checklist

Use this checklist for PRs in this area:

```text
Does the change preserve the receipt gate?
Does any LLM or retrieval output gain authority it should not have?
Does core learn domain-specific ESG facts?
Does profile-active behavior have a deterministic fingerprint?
Does the receipt or replay trace preserve the fingerprint that matters?
Does the canonical scenario still prove the closed authority loop?
Are tests focused on authority boundaries instead of incidental JSON shape?
```
