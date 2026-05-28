# Trust Kernel Hardening Standard

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-28
Can block PRs: yes

Checked anchors:
- code: comp/judgment/commit.py
- code: comp/judgment/receipts.py
- code: comp/compiler_tool/commit_flow.py
- code: comp/compiler_tool/receipt_builder.py
- code: comp/compiler_tool/profile_runner.py
- code: comp/compiler_tool/profiles.py
- test: tests/test_receipt_gated_projection.py
- test: tests/test_commit_receipt_builder.py
- test: tests/test_tiny_domain_fixture.py::test_compile_with_profile_merges_profile_baseline_and_rule_obligations
- test: tests/test_package_smoke.py::test_trust_kernel_hardening_documents_projection_numeric_policy
- test: tests/test_package_smoke.py::test_trust_kernel_hardening_documents_profile_baseline_policy

Freshness triggers:
- receipt-gated projection behavior changes
- `PublicOutputReceipt` or `PublicOutputValueCommitment` schema changes
- commit package, governance decision, or receipt builder behavior changes
- `CompilerProfile`, `compile_with_profile`, or `run_profile_rules` behavior changes
- trust-kernel/domain boundary public surface changes

Stale-language policy:
- current-status: strict
- future-work: allowed only under explicit non-goal, review, or promotion sections

This document fixes the implementation standard for trust-kernel hardening. The
goal is to keep `comp` as a small trust kernel rather than letting it drift back
into an ESG row generator.

This standard sits under the broader
`trust-kernel-extension-rings.md` architecture frame. In that frame, hardening
is the first phase: keep the trust kernel small, keep outer rings
non-authoritative, and preserve the authority promotion path through deterministic
gates.

The reviewable compiler/domain boundary is consolidated in
`compiler-domain-boundary.md`.

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
ReferenceOption != CanonicalReference
Retrieval score != truth score
Embedding top-1 != selected reference
LLM worker output != public authority
CalculatedClaim != public output
ValidationReport != public authority
ReviewDecision != public authority
PublicOutputReceipt == public projection authority
```

Accepted reports, commit packages, and governance decisions may explain why a
projection is close to publishable. They must not authorize projection without a
clean `PublicOutputReceipt`.

## Core / Domain Boundary

Core code must own protocol, not ESG meaning.
For the reviewable compiler/domain contract, see
`compiler-domain-boundary.md`.

Raw claim promotion is a domain-layer operation. A promotion helper may turn
supported extractor candidates into `CheckedClaim`, `CanonicalReference`,
`CalculatedClaim`, and `CalculationTrace` artifacts, but the promoted
`ValidationReport` still cannot authorize projection. `PublicOutputReceipt` remains the
only public projection authority.

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

`CompilerTool` should not learn ambient ESG meaning. Domain behavior must be
explicit at construction time, through a validated `CompilerProfile`, or through
domain-pack fixtures that are cited by the receipt/replay path.

When a `CompilerProfile` is used as the behavior lock, domain packs may declare
the `CompilerTool` baseline policy that would otherwise be constructor input:
known claim fields and allowed units. `compile_with_profile` must apply that
profile-declared baseline before merging profile-active rule obligations.
`run_profile_rules` remains the profile-only obligation runner and must not be
treated as a complete compiler baseline.

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
domain-pack compiler baseline known fields and allowed units
```

The fingerprint must be canonical and deterministic. Changing any active
behavior input should change the fingerprint digest.

Current implementation keeps profile declarations, domain-pack declarations,
formula declarations, reference records, and reference catalog snapshots as
explicit dependency fingerprints when they influence the receipt.
Readable lock manifests are replay substrate; they help explain the behavior
universe, but they do not become public authority.

## Projection Numeric Value Policy

The calculator should preserve exact numeric trace material while keeping public
projection values compatible with JSON-like projection rows.

Current policy:

```text
CalculationStep.exact_output_value preserves the Decimal value after the
formula rounding policy is applied.

CalculatedClaim.value is the public-row-compatible rounded value (`int` or
finite `float`) that becomes the source for PublicOutputValueCommitment.

PublicOutputValueCommitment hashes the committed public value with typed canonical
encoding. Replay checks the materialized public row against that commitment.
```

This means the trace explains the exact calculation and rounding decision, while
the receipt commits to the actual public projection value. If a future policy
chooses `Decimal` or canonical strings for public values, it must update this
contract, projection commitment tests, and scenario expectations together.

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

Current implementation keeps this small: scenario receipts and replay reports
expose the relevant profile, domain, formula, reference, and catalog
fingerprints. A full candidate graph belongs in a separate provenance contract,
not in this hardening standard.

## Canonical Trace Product

The canonical scenario should remain the representative trace product for the
project. It should show this full loop:

```text
raw evidence
-> deterministic extractor fixture
-> ValidationReport obligations
-> retrieval candidates
-> deterministic CanonicalReference
-> CalculationTrace / CalculatedClaim
-> ReviewPackage
-> ReviewDecision
-> PublicOutputReceipt
-> build_public_output
-> persistence replay
-> readable dependency manifests
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
durable production ledger policy
```

Durable ledger and backend policy belong in
`persistence-ledger-boundary.md`. This standard only requires that receipt and
replay payloads know what behavior and reference universe they are recording.

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
