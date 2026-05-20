# Extension Port Contracts

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-20
Can block PRs: yes

This document defines how outer-ring extensions attach to the `comp` trust
kernel without gaining authority. It is a companion to
`trust-kernel-extension-rings.md`.

The governing rule is simple:

```text
A port adapts external capability into submitted artifacts or stored artifacts.
A deterministic gate promotes authority.
A port is not a gate.
```

## Common Terms

Use these terms consistently when adding ports or reviewing PRs:

```text
candidate artifact
  Non-authoritative output proposed by an extractor, parser, resolver, or
  retriever.

submitted artifact
  Non-authoritative output delivered to the compiler gate for validation.

canonical artifact
  Artifact promoted by a deterministic gate, such as ReferenceBinding or
  DerivedClaim.

receipt authority
  Authority held by CommitReceipt for a specific projection scope.

view artifact
  Rendered or replayed explanation. It helps humans inspect authority, but does
  not create authority.
```

## Global Contract Rules

All extension ports must follow these rules:

```text
Ports may produce candidate, submitted, stored, or view artifacts.
Ports must not produce canonical authority artifacts directly.
Ports must preserve enough provenance for the compiler or replay layer to audit
their output.
Ports must make abstention or no-result states explicit.
Ports must keep backend scores, model confidence, UI state, and storage success
non-authoritative.
```

Forbidden direct outputs from outer-ring ports:

```text
CheckedClaim
ReferenceBinding
DerivedClaim
CommitPackage
GovernanceDecision
CommitReceipt
PublicProjection
```

If a backend appears to need one of these outputs, add a submitted artifact and a
deterministic gate instead.

## ExtractorPort

Extractor ports turn source material into evidence and candidates.

```python
class ExtractorPort(Protocol):
    def extract(self, source_unit: SourceUnit) -> tuple[CandidateArtifact, ...]:
        ...
```

Allowed outputs:

```text
EvidenceWitness
ClaimHypothesis
ReadingCandidate
ParseDerivation
TableCellCandidate
AmbiguitySet
```

Required provenance:

```text
source unit id
source reference
span or cell reference when available
extractor id and version
parse/config fingerprint when behavior affects candidates
```

Extractor ports must preserve ambiguity. A parser may say "these are possible
readings"; it must not decide that a claim is checked, a factor is bound, or a
row is public.

## ResolverWorker

Resolver workers consume work orders and submit resolution artifacts.

```python
class ResolverWorker(Protocol):
    def run(self, work_order: WorkOrder) -> WorkerResult:
        ...
```

Allowed outputs:

```text
SemanticJudgment
ReferenceQuery
EvidenceLink
ContextAttachment
AbstentionArtifact
HumanReviewQuestion
ConflictFlag
```

Required behavior:

```text
respect the work order allowed tool menu
return forbidden outputs as abstentions or validation failures
include cited spans, source ids, or rationale fields required by the obligation
make abstention explicit when the worker cannot satisfy the obligation
```

Resolver workers do not mutate `CompileReport`. They submit artifacts that the
compiler gate may accept, reject, or turn into new obligations.

## ReferenceResolver

Reference resolvers search a reference universe and return candidate-only
results.

```python
class ReferenceResolver(Protocol):
    def search(
        self,
        query: ReferenceQuery,
        *,
        limit: int = 10,
    ) -> tuple[ReferenceCandidate, ...]:
        ...
```

The only allowed output is:

```text
ReferenceCandidate
```

Required metadata:

```text
query id
retrieval lens
reference type when constrained
retrieval method
retrieval score when available
reference db version when available
index version when available
embedding model id when available
source witness ids when available
```

Non-negotiable invariants:

```text
ReferenceCandidate != ReferenceBinding
Retrieval score != truth score
Embedding top-1 != selected reference
```

Reference binding remains the job of deterministic selection against canonical
reference records and profile-active criteria.

## ProfileProvider And DomainPackProvider

Profile and domain-pack providers load behavior declarations. They do not
activate behavior by existence alone.

```python
class ProfileProvider(Protocol):
    def get_profile(self, profile_id: str) -> CompilerProfile:
        ...


class DomainPackProvider(Protocol):
    def get_domain_pack(self, domain_id: str, version: str) -> DomainPack:
        ...
```

Required behavior:

```text
return explicit versions
preserve declaration fingerprints
validate active ids against available declarations
avoid auto-activating installed rules, rubrics, retrieval policies, or projection
policies
```

The active `CompilerProfile` is the behavior lock. Receipts and replay reports
should cite the profile/domain behavior that influenced the projection.

## ArtifactStore

Artifact stores persist replay substrate. They do not interpret authority.
The builder contract for producing replay substrate lives in
`artifact-envelope-builder.md`.

```python
class ArtifactStore(Protocol):
    def record(self, envelope: ArtifactEnvelope) -> ArtifactEnvelope:
        ...

    def get(self, artifact_id: str) -> ArtifactEnvelope:
        ...
```

Required behavior:

```text
verify envelope body digest before recording
reject conflicting content for an existing artifact id
return stored envelopes without rewriting their body
preserve artifact kind and schema version
```

Forbidden behavior:

```text
minting CommitReceipt
changing projection values to match a receipt
treating storage success as projection authority
```

## ReceiptLedger

Receipt ledgers store receipt roots.

```python
class ReceiptLedger(Protocol):
    def record(self, receipt: CommitReceipt) -> CommitReceipt:
        ...

    def get(self, key: ReceiptLedgerKey) -> CommitReceipt:
        ...
```

Required behavior:

```text
key receipts by public row id, projection id, and draft/package id
reject conflicting receipts for the same ledger key
preserve receipt citations and barrier snapshot exactly
```

The ledger records authority that was already minted by the receipt builder. It
does not create authority.

## ReplayEngine

Replay engines verify that stored views can be explained by receipt-cited
artifacts.

```python
class ReplayEngine(Protocol):
    def replay_public_projection(
        self,
        row: Mapping[str, Any],
        projection: ProjectionSpec,
        *,
        receipt: CommitReceipt,
    ) -> ProjectionReplayReport:
        ...
```

Allowed output:

```text
ProjectionReplayReport
```

Replay reports must remain explanation artifacts. They may prove that a stored
row matches the receipt-authorized view, but they do not replace the receipt as
authority.

## ProductShell

Product APIs, CLIs, and UIs are view and routing surfaces.

Allowed behavior:

```text
display evidence and candidates
display open obligations and resolver tasks
submit resolver artifacts
display receipts and replay reports
route commit preparation requests to the trust kernel
```

Forbidden behavior:

```text
deciding commit status from UI state
directly calling public projection without a CommitReceipt
treating viewer JSON as authority
turning LLM text into public fields without compiler validation
```

## Testing Expectations

Each new port implementation should include tests for:

```text
allowed output shape
forbidden authority output
provenance fields needed by downstream validation
empty/no-result/abstention behavior
conflict handling when a stored or returned artifact disagrees with existing
state
```

Scenario tests should assert authority boundaries, not backend internals. For
example, a retrieval backend test should prove that candidates remain
candidate-only and that deterministic selection is still required for binding.

## Review Checklist

Use this checklist when adding a port or backend:

```text
Does the port return only candidate, submitted, stored, or view artifacts?
Does a deterministic gate still perform every authority promotion?
Is backend score or confidence clearly non-authoritative?
Can the output be audited through source ids, spans, versions, or fingerprints?
Does the no-result path create an obligation or abstention instead of pretending
success?
Does persistence preserve artifacts and receipts without rewriting authority?
Does the UI/API render and route rather than decide?
```
