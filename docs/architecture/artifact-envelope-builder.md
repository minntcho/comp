# Artifact Envelope Builder

Status: active-contract
Owner: persistence
Last checked against code: 2026-05-20
Can block PRs: yes

This document defines the contract for turning a completed compiler run into
the `ArtifactEnvelope` set needed for receipt replay.

It sits below `trust-kernel-extension-rings.md`,
`extension-port-contracts.md`, and `persistence-ledger-boundary.md`.

The builder exists to answer one question:

```text
Given a PublicOutputReceipt, which artifact envelopes must exist so replay can
explain the receipt-authorized public projection?
```

The builder does not mint receipts, repair missing evidence, recompute claims,
or decide authority. It packages already-promoted artifacts and already-cited
dependencies into replay substrate.

## Core Rule

```text
PublicOutputReceipt is authority.
ArtifactEnvelope is integrity and replay substrate.
Builder output is not authority.
```

If an artifact is cited by the receipt, the builder must either produce the
matching envelope or fail loudly. It must not silently omit, synthesize, or
rewrite cited material.

## Inputs

The production builder should accept the smallest set that can explain a
committed projection:

```text
ValidationReport
CommitPreparation
EvidenceRef artifacts used by checked claims
SemanticJudgment artifacts used to resolve semantic obligations
Dependency manifests for profile, domain, formula, source evidence, reference
records, and reference catalog snapshots
```

The current Domain Scenario Lab already has a fixture-shaped version of this
boundary in `tests/domain_scenarios/persistence.py`. Production code should
generalize that contract without making scenario fixtures authoritative.

## Outputs

The builder returns an artifact set keyed by `(artifact_kind, artifact_id)` or
records the same envelopes into an `ArtifactStore`.

Expected envelope kinds:

```text
evidence_witness
checked_claim
semantic_judgment
reference_binding
derived_claim
calculation_trace
formula
commit_package
governance_decision
compiler_profile
domain_pack
calculation_formula
reference_record
reference_catalog_snapshot
```

The builder may include extra diagnostic envelopes, but receipt replay must not
depend on uncited diagnostic material.

## Required Envelope Rules

Every envelope must satisfy the base `ArtifactEnvelope` contract:

```text
artifact_id is stable and non-empty
artifact_kind is stable and non-empty
schema_version is explicit
body_digest is computed from artifact kind, schema version, and body
body contains the minimum fields needed for replay validation
source_refs and meta remain explanatory, not authoritative
```

`ArtifactEnvelope.from_body(...)` is the canonical construction shape for now.
Backend-specific stores may persist envelopes differently, but they must preserve
the same digest semantics.

## Envelope Body Minimums

### evidence_witness

Minimum body:

```text
witness_id
field
source
span
text or source span digest when available
fingerprint
digest_alg
```

Replay uses this to verify checked claim witnesses and source evidence
fingerprints. If the original source text cannot be stored, the body must retain
the strongest available source/span digest and source reference.

### checked_claim

Minimum body:

```text
claim_id or stable checked_claim source id
field
value
witness_id
origin
```

The `value` field is required when the claim is the source of a
`PublicOutputValueCommitment`.

### semantic_judgment

Minimum body:

```text
judgment_id
obligation_id
verdict
rubric_id
judge
cited_span_ids
rationale
confidence when provided
```

The body should preserve enough protocol fields for replay or audit to explain
why the compiler accepted or rejected the judgment. The judgment remains a
resolver artifact, not public authority.

### reference_binding

Minimum body:

```text
binding_id
claim_id
reference_id
reference_type
selected_candidate_id
selector_rule_id
source_witness_ids
rejected_candidates
authority
```

Replay should be able to show the selected canonical reference and the rejected
near misses that explain deterministic selection.

### derived_claim

Minimum body:

```text
claim_id
field
value
unit
formula_id
trace_id
origin
```

The `value` field is required when the derived claim is the source of a
`PublicOutputValueCommitment`.

### calculation_trace

Minimum body:

```text
trace_id
formula_id
input_claim_ids
reference_binding_ids
steps
```

Each step should preserve:

```text
step_id
operation
input_ids
output_value
output_unit
```

### formula

Minimum body:

```text
formula_id
```

When a formula declaration fingerprint is available, prefer the richer
`calculation_formula` dependency envelope below.

### commit_package

Minimum body:

```text
package_id
subject_id
report_status
complete
checked_claim_fields
checked_claim_witness_ids
reference_binding_ids
derived_claim_ids
calculation_trace_ids
formula_ids
open_obligation_ids
resolved_obligation_ids
hazard_ids
profile_id
```

Commit packages are not public authority, but replay needs them to explain the
receipt barrier.

### governance_decision

Minimum body:

```text
decision_id
package_id
subject_id
status
reasons
profile_id
```

Governance decisions do not authorize projection without a clean
`PublicOutputReceipt`, but they are receipt issuance preconditions.

### compiler_profile

Minimum body:

```text
dependency_kind
dependency_id
fingerprint
digest_alg
profile_lock
```

`profile_lock` must be the canonical profile lock body used to compute the
fingerprint. Replay may recompute this fingerprint and fail if it differs.

### domain_pack

Minimum body:

```text
dependency_kind
dependency_id
fingerprint
digest_alg
domain_id
version
rule_families
rubrics
judge_policies
retrieval_query_policies
disabled_core_invariants
```

Domain-pack envelopes explain the domain behavior universe. Installed domain
packs are not active unless the compiler profile activates their declarations.

### calculation_formula

Minimum body:

```text
dependency_kind
dependency_id
fingerprint
digest_alg
formula_id
output_field
output_unit
factor_value_attribute
input_unit_attribute
output_unit_attribute
```

Formula envelopes explain the calculation behavior cited by traces and derived
claims.

### reference_record

Minimum body:

```text
dependency_kind
dependency_id
fingerprint
digest_alg
reference_id
reference_type
labels
aliases
description
attributes
source
witness_ids
```

Reference-record envelopes pin the canonical reference row used by a binding.

### reference_catalog_snapshot

Minimum body:

```text
dependency_kind
dependency_id
fingerprint
digest_alg
snapshot_id
catalog_id
catalog_version
record_fingerprints
```

When both reference records and catalog snapshots are cited, replay must verify
that the snapshot covers the cited records.

## Receipt Coverage

The builder should derive required envelopes from `receipt_artifact_refs(...)`.
That keeps the envelope set aligned with the receipt citation model.

Required coverage:

```text
every projection value commitment source artifact
every checked claim witness
every semantic judgment id
every reference binding id
every derived claim id
every calculation trace id
every formula id
every dependency fingerprint id
commit package id
governance decision id
```

If the receipt cites an artifact id that the builder cannot resolve, the builder
must fail. Missing cited artifacts are replay blockers, not warnings.

## Failure Modes

The builder should make these failures explicit:

```text
missing receipt
missing receipt citations
missing cited artifact
artifact kind mismatch
duplicate artifact id with conflicting body
projection value source lacks value
dependency fingerprint body cannot be produced
source evidence witness lacks replayable source/span material
```

It must not:

```text
invent projection values
drop open obligations from a package body
create synthetic CanonicalReference
create synthetic CalculatedClaim
mint PublicOutputReceipt
rewrite a stored envelope body to match a receipt
```

## Replay Contract

The output of the builder should be sufficient for:

```text
replay_public_projection(...)
verify_materialized_public_projection(...)
verify projection value commitments
verify dependency fingerprint sources
verify source evidence fingerprints
verify reference catalog snapshot coverage
```

If replay requires data that the builder does not preserve, the builder contract
is incomplete and should be updated before adding another backend.

## Testing Expectations

Tests for the first production builder should cover:

```text
all receipt_artifact_refs have envelopes
all envelope body digests verify
projection value commitment sources include matching value fields
profile lock fingerprint recomputes from profile_lock body
reference catalog snapshot covers cited reference records
missing cited artifact fails replay
tampered envelope body fails replay
builder does not create receipt authority
```

Domain Scenario Lab may keep using fixture builders, but scenario tests should
exercise the same contract so production and fixture replay do not drift apart.

## Review Checklist

Use this checklist for PRs that add or change envelope builders:

```text
Does the builder derive required artifacts from receipt citations?
Does every envelope body contain the fields replay checks need?
Does the builder preserve values used by PublicOutputValueCommitment?
Does the builder fail when cited artifacts are missing?
Does the builder avoid minting receipts or promoting authority?
Does replay still fail on tampered values, fingerprints, or artifact kinds?
Does the PR update this contract when a new receipt-cited artifact kind appears?
```
