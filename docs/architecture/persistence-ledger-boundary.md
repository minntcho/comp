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

The current implementation now has the first in-memory replay substrate:

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

comp.persistence
  ArtifactEnvelope + canonical artifact_digest
  InMemoryArtifactStore
  InMemoryReceiptLedger
  replay_public_projection(...)
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

Current additional layer:

```text
ReferenceCatalogSnapshot
  catalog_id
  catalog_version
  selected reference record fingerprints
  replay coverage check for cited reference records
```

Later layers may add:

```text
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

Those decisions should come after the in-memory replay substrate is exercised by
the canonical scenario harness.

---

## 11. Current Implementation Status

The first persistence slice is implemented:

```text
docs/architecture/persistence-ledger-boundary.md
  defines replay vs recompute, storage categories, and receipt-as-root.

comp/persistence/digest.py
comp/persistence/envelope.py
  provide canonical artifact body digests and ArtifactEnvelope.

comp/persistence/ledger.py
  provides InMemoryArtifactStore, InMemoryReceiptLedger, append-only receipt
  root semantics, and materialized projection verification.

comp/persistence/replay.py
  derives ArtifactRef items from CommitReceipt citations and replays a public
  row by checking receipt value commitments plus cited artifact envelopes.

tests/support/persistence_cases.py
  keeps persistence test setup readable without hiding negative mutation cases.

tests/domain_scenarios/persistence.py
  records receipt-cited scenario artifacts into an in-memory artifact store,
  records the CommitReceipt into an in-memory receipt ledger, and replays the
  materialized scenario projection from those stored envelopes.

CompilerProfile / DomainPack / RuleFamily / SemanticRubric fingerprints
  expose stable declaration fingerprints for the active profile and domain
  declaration world. CommitReceiptCitations can carry these dependency
  fingerprints, and replay reports surface the profile/domain/rule world the
  receipt depended on.

CalculationFormula / ReferenceRecord fingerprints
  expose stable declaration fingerprints for formulas and selected canonical
  reference rows. This lets replay explain both the calculation formula world
  and the reference world behind derived claims.

EvidenceWitness fingerprints
  expose stable source evidence fingerprints for checked claim witnesses. Replay
  can recompute the witness source/span/text fingerprint from the stored
  evidence witness artifact and block if the source span drifts.

Dependency fingerprint envelopes
  replay treats dependency fingerprints as receipt-cited artifact refs. The
  stored dependency envelope must exist, match the dependency kind/id, pass body
  digest verification, and carry the same fingerprint and digest algorithm as
  the receipt citation.

ReferenceCatalogSnapshot manifests
  replay treats catalog snapshots as receipt-cited dependency artifacts. When a
  receipt cites both a catalog snapshot and selected reference record
  fingerprints, the snapshot envelope must include those selected record
  fingerprints in its manifest.
```

The implemented minimum behavior is:

```text
ArtifactEnvelope body digest is stable canonical JSON.
Changing body changes digest.
Changing metadata does not change digest.
CommitReceipt can be recorded as an append-only ledger root.
Materialized public projection is treated as a view, not authority.
Replay verifies projection values against receipt commitments.
Replay blocks when an artifact body or projected value no longer matches its digest.
Replay verifies committed public values against the cited checked/derived source
artifact body, not only against the materialized row.
The canonical raw-input working loop can be replayed from stored scenario
artifact envelopes and its receipt ledger root.
Replay reports dependency fingerprints cited by the receipt, starting with the
compiler profile declaration, domain pack declarations, calculation formula
declarations, and selected reference records.
Replay blocks when a cited dependency fingerprint envelope is missing or its
stored fingerprint no longer matches the receipt citation.
Replay blocks when a cited reference catalog snapshot omits a selected
reference record fingerprint required by the receipt.
Replay blocks when a cited evidence witness artifact no longer matches the
source/span/text fingerprint cited by the receipt.
The L-Energy scenario records and replays the same dependency fingerprint shape,
including the retrieval-backed reference world, formula declaration world, domain
pack declaration world, and near-miss candidates.
The canonical raw-input working loop records and replays evidence witness
fingerprints for the raw text spans that grounded checked claims.
```

That completes the original in-memory substrate slice and attaches it to the
canonical raw-input and L-Energy scenario harnesses. It does not yet mean
production persistence exists, nor does it mean a database, retention policy, or
production catalog snapshot store exists.

---

## 12. Next Implementation Slice

Recommended next code slice:

```text
feat: export receipt proof graph
```

The graph boundary is now defined in `receipt-proof-graph.md`. The short rule is:

```text
Receipt authorizes.
Replay verifies.
Graph explains.
UI renders.
```

Candidate files:

```text
comp/explanation/*.py
tests/domain_scenarios/*.py
tests/domain_scenarios/views.py
tests/test_persistence_projection_replay.py
```

Minimum behavior:

```text
Replay reports or scenario views expose a graph-friendly edge list:
source evidence -> evidence witness -> checked claim -> derived claim -> receipt.
Dependency fingerprints appear as typed nodes with digest metadata.
Viewer payloads can answer why a public field exists without re-running the
compiler.
```

Non-goals for that slice:

```text
no database
no ORM
no production storage backend
no catalog ingestion pipeline
no legal retention policy
no full event sourcing
no real embedding index persistence
no production catalog snapshot store
no real DB ingestion
```

The goal is to move from "receipt pins all major dependency worlds" toward
"receipt replay can be rendered as a readable proof graph."

---

## 13. Following Slice

After dependency graph export, the next likely slice is source container
fingerprints:

```text
source container fingerprints
source document/version ids
replay verification for source container digests
```

That slice should keep the document's rule: replay explains the old receipt,
while recompute may produce a new answer under today's catalog and profile.
