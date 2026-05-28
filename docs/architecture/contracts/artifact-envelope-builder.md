# Artifact Envelope Builder

Status: active-contract
Owner: persistence
Last checked against code: 2026-05-28
Can block PRs: yes

Checked anchors:
- code: comp/persistence/envelope.py
- code: comp/persistence/envelope_builder.py
- code: comp/runtime/compiler_run_artifacts.py
- test: tests/test_artifact_envelope_builder.py
- test: tests/test_compiler_run_artifact_materializer.py
- test: tests/test_package_smoke.py::test_artifact_envelope_builder_contract_separates_coverage_from_materialization

Freshness triggers:
- `ArtifactEnvelope` schema, digest, or store behavior changes
- `ReceiptEnvelopeSetBuilder` coverage behavior changes
- `CompilerRunArtifactMaterializer` material source behavior changes
- domain scenario replay materialization boundary changes

Stale-language policy:
- current-status: strict
- future-work: allowed only under explicit review or promotion sections

This document defines the contract for producing the `ArtifactEnvelope` set
needed for receipt replay without letting persistence learn compiler internals.

It names two separate roles:

```text
ReceiptEnvelopeSetBuilder
  compiler-object agnostic coverage builder

CompilerRunArtifactMaterializer
  compiler-run adapter that can produce artifact material
```

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

## Role Split

The receipt coverage builder is compiler-object agnostic.

`ReceiptEnvelopeSetBuilder` consumes a `PublicOutputReceipt` and prepared
artifact material keyed by `(artifact_kind, artifact_id)`. It derives required
coverage from `receipt_artifact_refs(...)`, builds or records matching
`ArtifactEnvelope` objects, and fails when cited material is missing or
inconsistent.

It must not accept `ValidationReport`, `CommitPreparation`, or `EvidenceRef` as direct inputs.
It must not import `comp.compiler_tool`, inspect report status, discharge
requirements, select references, calculate claims, or decide public projection
authority.

`CompilerRunArtifactMaterializer` is a separate adapter. A compiler-run materializer may read compiler objects and produce artifact material.
It may serialize checked claims, semantic judgments, canonical references,
calculation traces, commit packages, governance decisions, dependency
fingerprints, and source evidence into replay-ready bodies.

The materializer is outside `comp.persistence` and must not mint receipts, discharge requirements, or decide projection authority.

## Inputs

The receipt coverage builder should accept the smallest compiler-agnostic set
that can explain a committed projection:

```text
PublicOutputReceipt
ArtifactMaterial items keyed by artifact_kind and artifact_id
optional ArtifactStore target
```

Domain Scenario Lab replay uses the production compiler-run materializer boundary.
Scenario fixture material must remain external material, not builder policy.
`tests/domain_scenarios/persistence.py` may enrich fixture-owned material as
`ExternalArtifactMaterialSource`, but it must not own receipt coverage,
`ArtifactEnvelope` construction, or projection authority.

A compiler-run materializer may accept the smallest compiler-aware set needed
to produce those materials:

```text
ValidationReport
CommitPreparation
EvidenceRef artifacts used by checked claims
SemanticJudgment artifacts used to resolve semantic requirements
Dependency manifests for profile, domain, formula, source evidence, reference
records, and reference catalog snapshots
```

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

## Current Implementation Status

The production receipt coverage builder lives in:

```text
comp.persistence.envelope_builder
```

`comp.persistence.envelope_builder` is a persistence module, not a compiler-run
adapter.

It exposes:

```text
ArtifactMaterial
ReceiptEnvelopeSetBuildError
build_receipt_envelope_set(...)
```

`build_receipt_envelope_set(...)` consumes a `PublicOutputReceipt` and
compiler-agnostic `ArtifactMaterial` items. It derives required refs from
`receipt_artifact_refs(...)`, verifies cited material coverage, builds
`ArtifactEnvelope` objects, and can optionally record the envelopes into a store
through a `record(...)` boundary.

The implementation does not import `comp.compiler_tool`, does not inspect
compiler reports, and does not produce compiler-run material.

The production compiler-run materializer lives in:

```text
comp.runtime.compiler_run_artifacts
```

`comp.runtime.compiler_run_artifacts` is a runtime adapter, not a persistence
module and not a receipt gate.

It exposes:

```text
CompilerRunArtifactMaterializationError
ExternalArtifactMaterial
ExternalArtifactMaterialSource
materialize_compiler_run_artifacts(...)
```

`materialize_compiler_run_artifacts(...)` consumes `ValidationReport`,
`CommitPreparation`, and an `ExternalArtifactMaterialSource`. It requires an
already-issued receipt on the preparation, derives the receipt refs, and returns
`ArtifactMaterial` for `build_receipt_envelope_set(...)`.

`ExternalArtifactMaterialSource` is a named external material boundary, not an authority source.
It supplies replay bodies for receipt-cited dependencies that are not owned by
the compiler run object graph.

The materializer may inspect compiler objects to serialize compiler-run
material. It must not mint receipts, call `build_public_output(...)`, record
envelopes, or decide projection authority.

Coverage lives in:

```text
tests/test_artifact_envelope_builder.py
tests/test_compiler_run_artifact_materializer.py
```

`tests/test_artifact_envelope_builder.py` pins the compiler-agnostic coverage
builder behavior. `tests/test_compiler_run_artifact_materializer.py` pins the
compiler-aware adapter behavior.

## Testing Expectations

Tests for the production builder should cover:

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

Domain Scenario Lab replay must exercise the same path:

```text
DomainScenarioResult
-> materialize_compiler_run_artifacts(...)
-> build_receipt_envelope_set(...)
-> replay_public_projection(...)
```

Scenario helpers may prepare fixture-owned external material, but they
must expose it as `ExternalArtifactMaterialSource`. They must not recreate `ArtifactEnvelope` construction or receipt-ref coverage
policy.

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
