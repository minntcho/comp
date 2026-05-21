# Production Trust Spine Database

Status: north-star
Owner: persistence
Last checked against code: 2026-05-21
Can block PRs: limited

This document sketches the production database direction for `comp`.

It is not a final database schema, migration contract, ORM design, or storage
backend decision. The table names and column shapes below are a working model
that may change as the product surface, replay engine, and domain packs evolve.

The stable part is the authority model:

```text
Artifact envelopes preserve replay material.
Commit receipts authorize public projection.
Registry snapshots pin the domain/reference/profile world.
Workflow state helps operators, but it is not authority.
Public projections are receipt-verified materialized views.
```

If a future schema changes table names, indexes, or storage mechanics, it should
keep those authority boundaries intact or update the active persistence
contracts explicitly.

## 1. Database Shape

Start with one Postgres database split by schemas:

```text
workflow
  case, source, obligation, task, and submission state

artifact
  artifact envelopes, artifact edges, and typed artifact indexes

ledger
  commit receipts, receipt commitments, dependency fingerprints, and receipt
  artifact refs

registry
  domain packs, compiler profiles, reference catalogs, formulas, projection
  specs, and artifact-kind schemas

projection
  public projection versions, current projection pointers, and replay reports
```

Use one database early because commit preparation, receipt insertion, projection
materialization, and replay bookkeeping benefit from one transaction boundary.
Large artifact bodies and source blobs may move to object storage later, but the
database should still hold stable digests, ids, and replay metadata.

## 2. Provisional Schema Rule

The production DB model is intentionally provisional.

The current code has an in-memory `ArtifactStore`, `ReceiptLedger`, and replay
engine. The production schema should grow from those contracts, but it should
not pretend that the first SQL draft is permanent.

Treat this document as a direction document:

```text
Stable:
  authority boundaries
  append-only receipt roots
  immutable receipt-cited artifact bodies
  replay/recompute separation
  version-pinned registry worlds

Expected to evolve:
  exact table names
  exact column sets
  JSONB vs normalized indexes
  typed artifact index coverage
  source blob storage mechanics
  replay report payload shape
```

A PR may deviate from the table sketches when it preserves the stable authority
model and explains the change.

## 3. Authority-Bearing Spine

The durable source of truth should be small:

```text
artifact.artifact_envelopes
ledger.commit_receipts
registry version locks and snapshots
```

Everything else should be treated as workflow state, an index, a cache, or a
view.

### Artifact Envelopes

`ArtifactEnvelope` is the base replay substrate. A production table should carry
the same meaning as the current dataclass:

```text
artifact_id
artifact_kind
schema_version
body_digest
body
source_refs
meta
```

Rules:

```text
Same artifact id + same digest is idempotent.
Same artifact id + different kind, schema, or digest is a conflict.
Receipt-cited artifact bodies are immutable.
Metadata is explanatory and must not change the body digest.
```

Avoid putting mutable ownership fields directly in the immutable envelope row.
Prefer link tables such as `artifact.case_artifact_links` when a case needs to
point at an artifact.

### Commit Receipts

`CommitReceipt` is the only public projection authority. A production ledger
row should preserve:

```text
receipt_id
public_row_id
projection_id
draft_id
winner_receipt_ids
authorized_fields
barrier_snapshot
citations
receipt_digest
issued_at
```

The current in-memory ledger key is:

```text
public_row_id + projection_id + draft_id
```

Production should keep that uniqueness rule and also introduce a stable
`receipt_id`, preferably derived from the canonical receipt body. Do not reuse
`public_row_id` as the receipt identity; one public row may have multiple
versions over time.

### Receipt Indexes

Store the full citations body, but also normalize the parts replay and
explanation need to query:

```text
ledger.receipt_value_commitments
ledger.receipt_dependency_fingerprints
ledger.receipt_artifact_refs
```

These tables are derived from the receipt. They must not become a second source
of truth. Receipt insertion should populate them in the same transaction, or a
database function should derive them from the canonical receipt body.

## 4. Workflow State

Workflow tables support product operation, not authority.

Expected tables:

```text
workflow.cases
workflow.source_units
workflow.source_spans
workflow.evidence_witnesses
workflow.proof_obligations
workflow.resolver_tasks
workflow.resolver_submissions
```

Important distinction:

```text
resolver_submissions are proposals.
accepted artifacts are produced by deterministic compiler gates.
```

LLM workers, human reviewers, importers, and UI actions may submit material for
validation. They must not directly insert canonical `ReferenceBinding`,
`DerivedClaim`, `CommitPackage`, `GovernanceDecision`, `CommitReceipt`, or
`PublicProjection` authority.

## 5. Registry State

Domain behavior should be versioned and replayable.

Expected registry areas:

```text
registry.domain_packs
registry.compiler_profiles
registry.compiler_profile_domain_packs
registry.reference_catalogs
registry.reference_catalog_versions
registry.reference_records
registry.reference_catalog_snapshot_records
registry.calculation_formulas
registry.projection_specs
registry.artifact_kind_schemas
```

Reference catalogs must be snapshot-oriented. Replay should not depend on a
mutable live reference row.

Compiler profiles are behavior locks. A receipt should cite the profile and
domain-pack fingerprints that made the projection meaningful.

Artifact bodies may use JSONB, but they should not be arbitrary JSON. The
registry should know which `artifact_kind + schema_version` pairs are accepted,
and replay should reject bodies that cannot satisfy the cited schema/digest
contract.

## 6. Projection State

Public projections are materialized views, not authority.

Use two layers:

```text
projection.public_projection_versions
  append-only materialized rows tied to receipts

projection.current_public_projections
  mutable pointer to the current version for a public row and projection
```

Changing a public row should create a new projection version and, when the
meaning changes, a new receipt. It should not mutate the old version in place.

Replay reports should be stored separately:

```text
projection.replay_reports
```

Replay reports explain whether a materialized projection verified against its
receipt and cited artifacts. They do not replace the receipt as authority.

## 7. Typed Indexes

Typed artifact indexes are useful for product queries, but they are not
authority.

Likely indexes:

```text
artifact.checked_claim_index
artifact.semantic_judgment_index
artifact.reference_candidate_index
artifact.reference_binding_index
artifact.calculation_trace_index
artifact.derived_claim_index
artifact.commit_package_index
artifact.governance_decision_index
```

These can arrive after the first durable spine. A typed index should be
rebuildable from artifact envelopes or inserted from the same compiler-core
transaction that records the envelope.

Domain-specific views follow the same rule. A PCF view, invoice-audit view, lab
QA view, or legal-proof view may make product queries fast, but each row must
remain connected to a receipt and replay path.

## 8. Role Boundaries

Database permissions should reinforce authority boundaries.

Recommended roles:

```text
app_user
  read cases and projections
  create workflow submissions
  no direct ledger or canonical artifact writes

resolver_worker
  read assigned tasks
  insert resolver submissions
  no canonical artifact writes

compiler_core
  insert artifact envelopes and typed indexes
  insert commit receipts and receipt-derived indexes
  materialize verified projection versions

domain_admin
  insert versioned registry entries
  no direct artifact, ledger, or projection authority writes

auditor
  read receipt, replay, artifact, and projection state
  no writes
```

If a backend needs broader permissions, review the extension-port contracts
before granting them.

## 9. MVP Order

Build the durable spine before the full product query surface.

V1 should prioritize:

```text
workflow.cases
workflow.source_units
workflow.source_spans
workflow.evidence_witnesses
workflow.proof_obligations
workflow.resolver_tasks
workflow.resolver_submissions

artifact.artifact_envelopes
artifact.artifact_edges

registry.domain_packs
registry.compiler_profiles
registry.reference_catalogs
registry.reference_catalog_versions
registry.reference_records
registry.artifact_kind_schemas
registry.projection_specs

ledger.commit_receipts
ledger.receipt_value_commitments
ledger.receipt_dependency_fingerprints
ledger.receipt_artifact_refs

projection.public_projection_versions
projection.current_public_projections
projection.replay_reports
```

V2 can add typed artifact indexes and domain-specific views once real product
queries make the required access patterns clear.

## 10. Non-Goals

This document does not settle:

```text
final migration files
ORM mappings
storage backend choice
object storage layout
legal retention policy
multi-region replication
event-sourcing strategy
real embedding index persistence
production LLM trace retention
```

Those decisions should be made after the first durable spine proves that a
receipt-authorized projection can be recorded, replayed, explained, and audited
without authority leaks.

## 11. Review Checklist

Use this checklist when adding production storage:

```text
Does the schema preserve CommitReceipt as the projection authority?
Are receipt-cited artifacts immutable or conflict-detected?
Can stored public rows be replayed from receipt-cited artifacts?
Are reference catalogs and profiles version-pinned?
Are workflow tables clearly non-authoritative?
Are typed indexes rebuildable from envelopes or inserted atomically with them?
Can domain-specific views trace every row back to a receipt?
Can resolver workers submit artifacts without promoting authority?
Does the PR avoid treating JSONB convenience bodies as untyped truth?
Does any schema change explain whether it updates this provisional model?
```

