# Friendly Authority Vocabulary

Status: north-star
Owner: trust-kernel
Last checked against code: 2026-05-22
Can block PRs: limited

This document proposes a friendlier vocabulary for onboarding, downstream
adapters, product surfaces, Korean documentation, and user-facing errors.

It is intentionally provisional. It does not rename code by itself, and it is
not yet an active contract. It becomes binding only when a follow-up PR updates
the code surface, compatibility aliases, tests, and examples together.

The stable part is the authority model:

```text
Candidates do not authorize calculation.
Calculated values do not authorize public output.
Review packages and decisions do not authorize public output by themselves.
Only a clean public-output receipt can authorize public output.
```

## 1. Problem

The current kernel names are precise for architecture review, but they are hard
for Korean onboarding and downstream product work.

```text
ClaimHypothesis
EvidenceWitness
ProofObligation
ReferenceBinding
DerivedClaim
CompileReport
CommitReceipt
ProjectionSpec
ArtifactEnvelope
```

Those names make sense after reading the architecture docs. They do not tell a
new operator, product engineer, or Korean user what action is needed.

The goal is not to translate Python identifiers into Korean. The goal is to keep
the kernel precise while giving users and downstream code names that reveal the
workflow.

## 2. Naming Surfaces

Use three separate surfaces:

```text
Canonical code name
  The preferred Python/API/schema name after migration.

Deprecated alias
  The old name kept temporarily for compatibility.

Display label
  Korean and product-facing text used in docs, CLI, UI, and errors.
```

Do not create a fourth authority surface. Aliases, labels, docs, and UI strings
must never decide whether a value can be calculated or publicly emitted.

## 3. Proposed Canonical Vocabulary

| Current name | Proposed canonical name | Korean display label | Authority note |
| --- | --- | --- | --- |
| `ClaimHypothesis` | `ClaimCandidate` | 검증 전 입력값 | Candidate only. It cannot be projected. |
| `EvidenceWitness` | `EvidenceRef` | 근거자료 위치 | Grounding reference for validation. It is not a value authority by itself. |
| `ProofObligation` | `ValidationRequirement` | 보완 필요 항목 | Work required before the report can become clean. |
| `ReferenceCandidate` | `ReferenceOption` | 기준 후보 | Retrieval result only. It cannot authorize calculation. |
| `ReferenceBinding` | `CanonicalReference` | 확정 기준 | Deterministically selected reference that may authorize calculation input. |
| `CalculationTrace` | `CalculationTrace` | 계산 내역 | Reproducibility record. Keep the current name. |
| `DerivedClaim` | `CalculatedClaim` | 계산값 | Calculated value. It still cannot authorize public output. |
| `CompileReport` | `ValidationReport` | 검증 결과 | Compiler result. It summarizes state but does not authorize projection. |
| `CommitPackage` | `ReviewPackage` | 승인 검토 묶음 | Frozen review bundle. It is a receipt precondition, not projection authority. |
| `GovernanceDecision` | `ReviewDecision` | 검토 결정 | Review result. Only a commit decision can lead to receipt issuance. |
| `CommitReceipt` | `PublicOutputReceipt` | 공개 승인 증표 | The receipt-gated public-output authority. |
| `CommitReceiptCitations` | `PublicOutputReceiptCitations` | 공개 승인 근거 | Receipt barrier snapshot and dependency citations. |
| `ProjectionSpec` | `PublicOutputSpec` | 공개 출력 정의 | Defines output shape. It does not authorize output. |
| `ProjectionBlocked` | `PublicOutputBlocked` | 공개 출력 차단 | Raised when public output lacks receipt authority. |
| `PublicProjection` | `PublicOutput` | 공개 결과 | Materialized output view. It is not authority by itself. |
| `ArtifactEnvelope` | `ArtifactEnvelope` | 감사 산출물 기록 | Keep the kernel name for digest-bound replay material. |

`ReferenceBinding` is the most sensitive rename. `SelectedReference` is easier
to read, but it can sound like a user simply picked one option. The kernel
meaning is stronger: the reference has been selected by deterministic checks and
can be used by calculation. `CanonicalReference` keeps that meaning.

`CommitReceipt` is also sensitive. `OutputReceipt` is easy, but too broad.
`ProjectionReceipt` is accurate, but reintroduces the hard word. This document
therefore proposes `PublicOutputReceipt`.

`ArtifactEnvelope` should keep its code name, but its Korean display label
should not be the broad term "감사 기록". That phrase can also describe receipt
ledger entries, review decisions, and replay reports. `ArtifactEnvelope` is the
schema-versioned, digest-bound wrapper for replay material, so the narrower
label is `감사 산출물 기록`.

## 4. Korean Display Registry

Product surfaces should not derive Korean labels from class names. They should
read from an explicit registry.

The first implementation lives in `comp.schema_labels`. It is intentionally a
display registry, not an authority module:

```python
from comp.schema_labels import SCHEMA_LABELS, schema_label_ko

schema_label_ko("ClaimCandidate")
# "검증 전 입력값"

SCHEMA_LABELS["ArtifactEnvelope"].ko
# "감사 산출물 기록"
```

The registry should live outside the authority decision path. It may help docs,
CLI output, UI labels, and downstream adapters. It must not decide validation,
calculation, receipt issuance, replay, or projection.

## 5. Error Message Policy

User-facing messages should describe the required action instead of leaking
kernel type names.

Avoid:

```text
ClaimHypothesis has no EvidenceWitness.
ReferenceCandidate cannot authorize calculation.
CommitReceipt is required for projection.
Replay failed due to source fingerprint mismatch.
```

Prefer:

```text
검증 전 입력값에 연결된 근거자료가 없습니다.
계산에 사용할 기준이 아직 확정되지 않았습니다.
공개 결과를 만들려면 공개 승인 증표가 필요합니다.
원본자료가 변경되어 감사 재검증에 실패했습니다.
```

The first helper lives in `comp.user_messages`:

```python
from comp.user_messages import user_message_for_reason, user_message_ko

user_message_for_reason("unsupported_unit").ko
# "지원하지 않는 단위입니다. 단위를 확인해 주세요."

user_message_ko("public_output_receipt_required")
# "공개 결과를 만들려면 공개 승인 증표가 필요합니다."
```

Like `comp.schema_labels`, this helper is display-only. It can be used by docs,
CLI output, UI adapters, and downstream product surfaces. It must not decide
validation, calculation, receipt issuance, replay, or public-output authority.

Internal exception types may remain English. Their messages should be suitable
for CLI and product display unless the exception is explicitly developer-only.

## 6. Migration Shape

Prefer canonical rename plus deprecated aliases over an alias-only onboarding
layer.

Alias-only migration:

```text
Pros:
  Low risk.
  Existing imports keep working.

Cons:
  New users still hit old names in docs, reprs, errors, tests, and examples.
  The repo keeps two vocabularies indefinitely.
  Downstream product code can accidentally expose old kernel terms.
```

Canonical rename with deprecated aliases:

```text
Pros:
  The public surface becomes easier.
  Existing users get a compatibility window.
  Tests and docs can enforce the new vocabulary.

Cons:
  The first PR touches more files.
  Type reprs, imports, serialization, and docs need careful migration.
```

Recommended migration order:

```text
1. Add the display-label registry and Korean-facing message helpers.
2. Update user-facing error messages to stop leaking hard kernel names.
3. Rename compiler-side intake and validation types:
   ClaimHypothesis -> ClaimCandidate
   EvidenceWitness -> EvidenceRef
   ProofObligation -> ValidationRequirement
4. Rename reference/calculation/report types:
   ReferenceCandidate -> ReferenceOption
   ReferenceBinding -> CanonicalReference
   DerivedClaim -> CalculatedClaim
   CompileReport -> ValidationReport
5. Rename review and public-output gate types:
   CommitPackage -> ReviewPackage
   GovernanceDecision -> ReviewDecision
   CommitReceipt -> PublicOutputReceipt
   ProjectionSpec -> PublicOutputSpec
   ProjectionBlocked -> PublicOutputBlocked
6. Keep deprecated aliases for one compatibility window.
7. Update README, docs, examples, and smoke tests to prefer new names.
```

Each migration PR should preserve the core authority assertions:

```text
ReferenceOption cannot authorize calculation.
CanonicalReference can authorize calculation input.
CalculatedClaim cannot authorize public output.
ReviewPackage cannot authorize public output.
ReviewDecision cannot authorize public output by itself.
PublicOutputReceipt is required for public output.
PublicOutput is a receipt-verifiable view, not authority.
```

## 7. Current Implementation Status

The first compiler-side names are now available as canonical Python objects
with deprecated aliases:

```text
ClaimCandidate is canonical.
ClaimHypothesis remains a compatibility alias.

EvidenceRef is canonical.
EvidenceWitness remains a compatibility alias.

ValidationRequirement is canonical.
ProofObligation remains a compatibility alias.

evidence_ref_fingerprint is canonical.
evidence_witness_fingerprint remains a compatibility alias.

ReferenceOption is canonical.
ReferenceCandidate remains a compatibility alias.

CanonicalReference is canonical.
ReferenceBinding remains a compatibility alias.

CalculatedClaim is canonical.
DerivedClaim remains a compatibility alias.

ValidationReport is canonical.
CompileReport remains a compatibility alias.

ReviewPackage is canonical.
CommitPackage remains a compatibility alias.

ReviewDecision is canonical.
GovernanceDecision remains a compatibility alias.

PublicOutputReceipt is canonical.
CommitReceipt remains a compatibility alias.

PublicOutputReceiptCitations is canonical.
CommitReceiptCitations remains a compatibility alias.

PublicOutputSpec is canonical.
ProjectionSpec remains a compatibility alias.

PublicOutputBlocked is canonical.
ProjectionBlocked remains a compatibility alias.

PublicOutput is available as the public-row return type.

build_public_output_receipt is canonical.
build_commit_receipt remains a compatibility alias.

comp.schema_labels provides frozen display metadata for the friendly public
surface. It is display-only and is not imported by the receipt gate, receipt
builder, or persistence replay boundary.
```

The underlying evidence fingerprint payload still uses
`dependency_kind="evidence_witness"` so existing receipt and replay dependency
digests stay stable during the rename window.

This step does not rename report fields such as `evidence_witnesses`,
`reference_candidates`, `reference_bindings`, `derived_claims`, or
`obligations`; those are compatibility surfaces for later, more careful PRs.

This step now renames the receipt, citation, output specification, and output
blocking error types. The old names remain compatibility aliases, but docs,
examples, and downstream product surfaces should prefer the public-output names.

## 8. Non-Goals

Do not use Korean Python class names.

Do not move ESG, LCA, PCF, or customer-specific words into the trust kernel.
Those names belong in domain packs, product adapters, scenario packs, or UI
copy.

Do not treat display labels as schema authority.

Do not use this rename to move receipt authority into reports, decisions, replay
reports, proof graphs, or public-output rows.

Do not rename persistence internals just to make them friendlier. Persistence
names must continue to protect digest, schema-version, replay, and append-only
ledger semantics.

## 9. Promotion Rule

While this document is a north star, it can guide naming review and onboarding
discussion, but it should not block unrelated PRs by itself.

Promote it to an active contract only after the first rename PR proves:

```text
Deprecated aliases keep compatibility.
New canonical names are exported and documented.
Korean labels and error messages do not affect authority decisions.
Receipt-gated projection tests still prove the public-output boundary.
```
