# Persistence / Ledger Boundary

CommitReceipt as the durable explanation root.

This document fixes the persistence boundary for the active `comp` rebuild. It
is not a database schema, ORM design, or production retention policy. Its goal
is to define which artifacts must survive after a run so a public projection can
be explained later without accidentally turning cached views or resolver output
into authority.

The short version:

```text
Public row is a view.
CommitReceipt is the ledger root.
Artifact envelopes are the replay substrate.
Fingerprints pin the world that made the receipt meaningful.
```

The current implementation already points in this direction:

```text
CommitReceipt
  projection_id
  authorized_fields
  CommitReceiptCitations
  projection_value_commitments

project_public_row(...)
  requires receipt
  requires clean citations
  checks projection id
  checks field scope
  checks value commitments
```

This document describes how that in-memory authority boundary should become a
durable explanation boundary.

---

## 1. Core Principle

The persistence question is not only:

```text
What should we store?
```

The stronger question is:

```text
What authority claim must still be verifiable months later?
```

`comp` should persist enough to answer:

```text
Why was this public projection authorized?
Which evidence, judgments, references, formulas, traces, profile, and domain
context made the receipt meaningful?
Has a materialized public row drifted from the receipt that authorized it?
```

It should not persist caches or convenience views in a way that gives them
authority.

---

## 2. Storage Categories

Use five categories when adding storage or deciding what an artifact means.

```text
scratch
  Disposable work product from extraction, retrieval, resolving, or draft
  compilation. It may be useful for debugging, but it is not required for
  replay after commit.

case record
  Immutable explanation material for a committed or reviewed case. These
  artifacts are not public projection authority by themselves, but a receipt may
  cite them.

ledger
  Append-only authorization root. In the current architecture this is
  CommitReceipt and the receipt barrier snapshot.

view
  Regenerable output for serving or inspection. A view may be stored for
  convenience, but it is invalid if it cannot be verified against its receipt.

index/cache
  Rebuildable operational acceleration: embedding indexes, retrieval caches,
  query materializations, and task queues. These can influence recall, not
  authority.
```

Rule of thumb:

```text
Scratch is disposable.
Case record is explainable.
Ledger is append-only.
View is receipt-verifiable.
Index/cache is rebuildable and never authoritative.
```

---

## 3. Replay vs Recompute

Replay and recompute must remain separate.

```text
Replay
  Stored receipt + cited artifact envelopes
  -> explain why the committed projection authorization was valid then.

Recompute
  Raw evidence + current compiler/profile/reference catalog
  -> produce a new candidate commit package now.
```

A `CommitReceipt` supports replay. It does not guarantee that current rules,
current references, or current retrieval behavior will recompute the same
result.

This matters because domain packs, profiles, reference catalogs, and retrieval
indexes are expected to evolve. A new compiler profile may produce a better
answer for the same raw evidence. That should not invalidate the ability to
explain an older receipt.

Therefore:

```text
Replay must use stored artifact envelopes and stored fingerprints.
Recompute may use current compiler/profile/catalog state and may differ.
```

---

## 4. Artifact Retention Table

| Artifact | Category | Persist? | Mutability | Authority | Replay role |
| --- | --- | --- | --- | --- | --- |
| Raw source reference | case record | yes, if cited | immutable after receipt citation | evidence location, not claim truth | locates the original source or source container |
| Source span digest | case record | yes, if available | immutable after receipt citation | evidence integrity | proves cited source text did not drift |
| EvidenceWitness | case record | yes | immutable after receipt citation | grounding for checked claims | connects checked claims to source/span |
| InterpretationHypothesis | scratch / case record | optional final only | immutable if cited | proposal only | explains what entered the compiler |
| ReferenceCandidate | scratch / cited case record | optional | discardable unless cited | none | only useful when cited by selection explanation |
| RejectedReferenceCandidate | case record inside binding | yes, if cited by binding | immutable after binding | selector explanation | explains near misses and rejection reasons |
| SemanticJudgment | case record | yes, if accepted | immutable after accepted | resolver artifact, not receipt authority | discharges semantic obligations |
| ReferenceBinding | case record | yes | immutable after commit | canonical reference binding | authorizes reference input to calculation |
| CalculationTrace | case record | yes | immutable after commit | calculation provenance | explains derived claim calculation |
| DerivedClaim | case record | yes | immutable after commit | calculated claim, not public authority | source of projection value commitment |
| CompileReport | case record | final only | immutable after commit | compiler result, not projection authority | summarizes checked claims, obligations, hazards, bindings, and derived claims |
| CommitPackage | case record | yes | immutable once cited | frozen commit candidate, not public authority | bundle digest cited by receipt |
| GovernanceDecision | case record / ledger-cited | yes | immutable | commit, hold, or reject decision | receipt issuance precondition |
| CommitReceipt | ledger | yes | append-only | projection authority | durable replay root |
| PublicProjection | view | optional | replaceable if receipt-verifiable | none | materialized output only |
| ReferenceRecord | case dependency | yes if used, or via snapshot | version-pinned | reference authority source | verifies binding context |
| ReferenceCatalog | case dependency | fingerprint or snapshot | version-pinned | reference authority collection | proves which reference world was used |
| CompilerProfile | case dependency | fingerprint plus optional snapshot | version-pinned | active behavior lock | explains active rules, rubrics, judge policy, and projection policy |
| DomainPack | case dependency | fingerprint plus optional snapshot | version-pinned | domain meaning source | explains domain rule context |
| Retrieval index | index/cache | operational only | rebuildable | none | recall trace only if cited separately |
| Resolver task queue state | index/cache | operational only | rebuildable | none | not part of receipt authority |

`CompileReport` needs special care. Draft reports are scratch/debug material.
The final report cited by a commit package is a case record.

`PublicProjection` also needs special care. Persisting a public row must not
make the row authoritative. If a stored row conflicts with the receipt value
commitments, the row is invalid.

---

## 5. CommitReceipt As Ledger Root

`CommitReceipt` should be the durable root of projection explanation, not a
container for every artifact body.

The receipt should carry or cite:

```text
receipt identity
public_row_id
projection_id
authorized_fields
governance decision id and digest
commit package id and digest
barrier snapshot
projection value commitments
profile fingerprint
domain pack fingerprints
reference record or catalog fingerprints
formula fingerprints
source evidence fingerprints
```

The current `ProjectionValueCommitment` design is the right shape:

```text
field
source_kind
source_id
value_digest
digest_alg
```

It fixes field values without copying raw values into the receipt. The receipt
can verify a materialized projection without becoming a second storage location
for public row values.

The long-term rule:

```text
CommitReceipt is the append-only authorization root.
Artifact envelopes hold the replay bodies.
Digest references connect the root to the replay graph.
```

---

## 6. Artifact Envelope Contract

The next implementation slice should introduce a small envelope contract before
choosing a database.

Candidate shape:

```python
@dataclass(frozen=True)
class ArtifactEnvelope:
    artifact_id: str
    artifact_kind: str
    schema_version: str
    body_digest: str
    body: Mapping[str, Any]
    source_refs: tuple[str, ...] = ()
    meta: tuple[tuple[str, Any], ...] = ()
```

The digest target must be stable:

```text
artifact_kind
schema_version
canonical body
```

Operational metadata must stay outside the digest:

```text
stored_at
writer
storage backend id
local path
debug label
run id
```

Do not include timestamps, local paths, or writer process details in the
canonical body digest. They make replay sensitive to storage mechanics instead
of artifact meaning.

Envelope rules:

```text
Changing the body changes the digest.
Changing metadata does not change the body digest.
An envelope cited by a receipt is immutable.
An envelope not cited by a receipt may be debug material, cache, or scratch.
```

---

## 7. Mutation Policy

Use this policy when deciding whether a persisted record may change.

```text
scratch
  May be overwritten, discarded, or compacted.

case record
  Mutable while a case is still draft.
  Immutable after a CommitReceipt cites it.

ledger
  Append-only.
  Corrections create a new receipt or superseding record.

view
  Replaceable if it remains verifiable against the receipt.
  Invalid if receipt verification fails.

index/cache
  Freely rebuildable and invalidatable.
  Must not be cited as authority unless converted into a case record artifact.
```

The important boundary:

```text
After receipt citation, update by appending, not mutating.
```

---

## 8. Replay Model

Replay should explain a committed projection without consulting the latest
domain pack, latest reference catalog, latest retrieval index, or latest LLM.

Target replay graph:

```text
CommitReceipt
  -> CommitPackage envelope
  -> GovernanceDecision envelope
  -> final CompileReport envelope
  -> EvidenceWitness / source evidence envelopes
  -> accepted SemanticJudgment envelopes
  -> ReferenceBinding envelopes
  -> ReferenceRecord or ReferenceCatalog fingerprints
  -> CalculationTrace envelopes
  -> DerivedClaim envelopes
  -> ProjectionValueCommitment verification
  -> PublicProjection view
```

Replay should answer:

```text
Was the receipt issued from a complete package?
Was governance status commit?
Were open obligations and hazards empty?
Which fields were authorized?
Which value digest was authorized for each projected field?
Which checked or derived artifact supplied each field?
Which evidence witnesses grounded the checked claims?
Which reference rows and formulas supported derived claims?
Which profile and domain pack versions made the rules meaningful?
```

Replay should not answer:

```text
Would today's compiler produce the same answer?
Would today's retrieval index recall the same candidates?
Would a newer domain pack choose the same projection?
```

Those are recompute questions.

---

## 9. Dependency Fingerprints

Reference and profile dependencies should be pinned gradually.

First practical layer:

```text
ReferenceBinding
  cites selected ReferenceRecord envelope or selected record digest

CompilerProfile
  exposes a declaration fingerprint:
    profile_id
    core_invariant_version
    domain pack ids / versions / fingerprints
    active_rule_ids
    active_rubric_ids
    judge_policy_id
    projection_policy_id
```

Do not try to hash arbitrary Python callables as the first implementation. Rule
and rubric ids, domain pack versions, package versions, and git revisions are
more realistic first pins.

Later layers may add:

```text
ReferenceCatalogSnapshot
  catalog_id
  catalog_version
  record_digests
  source
  effective_date

DomainPackFingerprint
  domain_id
  version
  rule ids / rubric ids / projection policy ids
  implementation package version or git revision
```

A `ReferenceBinding` should be replayable against either the exact selected
`ReferenceRecord` envelope or a catalog snapshot manifest that contains the
selected record digest.

---

## 10. Non-Goals

This document does not define:

```text
production database schema
ORM mappings
storage backend choice
distributed consensus
legal retention policy
full event sourcing
real embedding index persistence
LLM trace retention policy
```

Those decisions should come after the artifact envelope and ledger boundary are
small enough to test in memory.

---

## 11. Next Implementation Slice

Recommended next code slice:

```text
feat: add artifact envelope and in-memory receipt ledger stub
```

Candidate files:

```text
comp/persistence/__init__.py
comp/persistence/digest.py
comp/persistence/envelope.py
comp/persistence/ledger.py
tests/test_persistence_ledger_boundary.py
```

Minimum behavior:

```text
ArtifactEnvelope body digest is stable canonical JSON.
Changing body changes digest.
Changing metadata does not change digest.
CommitReceipt can be recorded as an append-only ledger root.
Materialized public projection is treated as a view, not authority.
Replay can verify projection values against receipt commitments.
Replay blocks when an artifact body or projected value no longer matches its digest.
```

Non-goals for that slice:

```text
no database
no ORM
no production storage backend
no catalog ingestion pipeline
no legal retention policy
no full event sourcing
```

The goal is to make the replay substrate testable before deciding where it
lives.
