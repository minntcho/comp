# Friendly Authority Vocabulary

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-22
Can block PRs: yes

This document defines the canonical friendly vocabulary for active comp authority
surfaces. The repo exposes only the canonical authority names.

The stable authority model is:

```text
Options do not authorize calculation.
Calculated values do not authorize public output.
Review packages and review decisions do not authorize public output by
themselves.
Only a clean public-output receipt can authorize public output.
```

## 1. Naming Surfaces

Use two separate surfaces:

```text
Canonical code name
  The Python/API/schema name used by active code, tests, docs, and examples.

Display label
  Korean and product-facing text used in docs, CLI, UI, and errors.
```

Do not create a third authority surface. Display labels, docs, and UI strings
must never decide whether a value can be calculated or publicly emitted.

## 2. Canonical Vocabulary

| Canonical code name | Korean display label | Authority note |
| --- | --- | --- |
| `ClaimCandidate` | 검증 전 입력값 | Candidate only. It cannot be publicly emitted. |
| `EvidenceRef` | 근거자료 위치 | Grounding reference for validation. It is not value authority by itself. |
| `ValidationRequirement` | 보완 필요 항목 | Work required before the report can become clean. |
| `ReferenceOption` | 기준 후보 | Retrieval result only. It cannot authorize calculation. |
| `CanonicalReference` | 확정 기준 | Deterministically selected reference that may authorize calculation input. |
| `CalculationTrace` | 계산 내역 | Reproducibility record. |
| `CalculatedClaim` | 계산값 | Calculated value. It still cannot authorize public output. |
| `ValidationReport` | 검증 결과 | Compiler result. It summarizes state but does not authorize public output. |
| `ReviewPackage` | 승인 검토 묶음 | Frozen review bundle. It is a receipt precondition, not public-output authority. |
| `ReviewDecision` | 검토 결정 | Review result. Only a commit decision can lead to receipt issuance. |
| `PublicOutputReceipt` | 공개 승인 증표 | The receipt-gated public-output authority. |
| `PublicOutputReceiptCitations` | 공개 승인 근거 | Receipt barrier snapshot and dependency citations. |
| `PublicOutputSpec` | 공개 출력 정의 | Defines output shape. It does not authorize output. |
| `PublicOutputBlocked` | 공개 출력 차단 | Raised when public output lacks receipt authority. |
| `PublicOutput` | 공개 결과 | Materialized output view. It is not authority by itself. |
| `PublicOutputValueCommitment` | 공개값 무결성 약정 | Digest commitment for values authorized by the receipt. |
| `ArtifactEnvelope` | 감사 산출물 기록 | Schema-versioned, digest-bound wrapper for replay material. |

`CanonicalReference` is intentionally not `SelectedReference`. The easier name
can sound like a person merely picked one option. The kernel meaning is
stronger: the reference has been selected by deterministic checks and can be
used by calculation.

`ArtifactEnvelope` keeps its code name because it is not a general audit log.
Its display label is `감사 산출물 기록`, not just `감사 기록`, because it describes
integrity-checkable replay material rather than receipts, review decisions, or
replay reports as a whole.

## 3. Korean Display Registry

Product surfaces should not derive Korean labels from class names. They should
read from an explicit registry.

The first implementation lives in `comp.schema_labels`. It is display-only:

```python
from comp.schema_labels import SCHEMA_LABELS, schema_label_ko

schema_label_ko("ClaimCandidate")
# "검증 전 입력값"

SCHEMA_LABELS["ArtifactEnvelope"].ko
# "감사 산출물 기록"
```

The registry may help docs, CLI output, UI labels, and downstream adapters. It
must not decide validation, calculation, receipt issuance, replay, or
public-output authority.

## 4. Error Message Policy

User-facing messages should describe the required action instead of leaking
kernel type names.

Avoid:

```text
ClaimCandidate has no EvidenceRef.
ReferenceOption cannot authorize calculation.
PublicOutputReceipt is required for projection.
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

## 5. Guardrails

Active package surfaces must use the canonical names above.

`tests/test_complete_friendly_rename.py` blocks the old authority names from
returning to active code, tests, docs, and examples. Historical snapshots under
`docs/archive/` may retain old names as archived context only.

Each PR that touches these surfaces must preserve the core authority assertions:

```text
ReferenceOption cannot authorize calculation.
CanonicalReference can authorize calculation input.
CalculatedClaim cannot authorize public output.
ReviewPackage cannot authorize public output.
ReviewDecision cannot authorize public output by itself.
PublicOutputReceipt is required for public output.
PublicOutput is a receipt-verifiable view, not authority.
```

## 6. Residual Field Vocabulary Audit

The canonical class and export names are complete. Some active fields, fixture
keys, and serialized receipt/replay payload keys still contain older vocabulary.
They must be handled by category, not by a global text replacement.

### Safe active field rename candidates

These are active Python-facing names that still expose older terms. They should
be renamed in a breaking follow-up PR when the call sites can move together:

| Current active field | Preferred field | Why it can move |
| --- | --- | --- |
| `ValidationReport.evidence_witnesses` | `ValidationReport.evidence_refs` | The value type is already `EvidenceRef`; this is an active object field, not receipt authority. |
| `ValidationReport.reference_candidates` | `ValidationReport.reference_options` | The value type is already `ReferenceOption`; this is compiler report state. |
| `ValidationReport.reference_bindings` | `ValidationReport.canonical_references` | The value type is already `CanonicalReference`; this is calculation input authority, not a free-form selection. |
| `ValidationReport.derived_claims` | `ValidationReport.calculated_claims` | The value type is already `CalculatedClaim`; this is report state and public-output precondition input. |
| `ValidationReport.obligations` | `ValidationReport.validation_requirements` | The value type is already `ValidationRequirement`; this field is user-visible enough to deserve the friendly name. |
| `ValidationReport.resolved_obligations` | `ValidationReport.resolved_validation_requirements` | Keeps the open/resolved pair aligned after `obligations` moves. |

Required shorthand for the next active-field PR:

```text
`ValidationReport.evidence_witnesses` -> `ValidationReport.evidence_refs`
`ValidationReport.reference_candidates` -> `ValidationReport.reference_options`
`ValidationReport.reference_bindings` -> `ValidationReport.canonical_references`
`ValidationReport.derived_claims` -> `ValidationReport.calculated_claims`
`ValidationReport.obligations` -> `ValidationReport.validation_requirements`
`ValidationReport.resolved_obligations` -> `ValidationReport.resolved_validation_requirements`
```

Do not add aliases for these fields unless a migration PR explicitly proves the
temporary duplicate surface cannot leak into docs, examples, or downstream
imports. The default migration shape is still a breaking rename.

### Codec-bound receipt and replay vocabulary

These names are serialized into receipts, barrier snapshots, proof graphs,
persistence rows, scenario fixtures, or replay material. They may be renamed,
but only through a codec/boundary PR that pins old-body replay behavior and
new-body output behavior together:

| Serialized or replay-facing name | Boundary |
| --- | --- |
| `PublicOutputReceipt.projection_id` | Receipt identity and replay lookup. |
| `PublicOutputReceiptCitations.projection_id` | Barrier snapshot equality check. |
| `PublicOutputReceiptCitations.projection_value_commitments` | Value digest proof surface. |
| `PublicOutputReceiptCitations.commit_package_id` | Receipt citation to the review package artifact. |
| `PublicOutputReceiptCitations.governance_decision_id` | Receipt citation to the review decision artifact. |
| `PublicOutputReceiptCitations.checked_claim_witness_ids` | Receipt citation to checked evidence spans. |
| `DependencyFingerprint.dependency_kind="evidence_witness"` | Existing dependency digest semantics. |

Changing these in the same PR as active report fields would mix API cleanup with
replay compatibility. That is exactly the kind of dual-SSOT risk this repo
tries to avoid.

### Terms intentionally not globally banned

Do not add a blanket ban on `projection` or `witness`.

`Projection` is no longer the class name for public output, but lowercase
`projection_id`, `public_projection` fixture names, and replay function names
still identify persisted or scenario-contract concepts. They need codec-aware
migration, not search-and-replace cleanup.

`Witness` is no longer part of `EvidenceRef`, but `witness_id`,
`source_witness_ids`, and `checked_claim_witness_ids` may still be protocol
identifiers for source spans and receipt citations. Rename them only when the
receipt, replay, and scenario-contract payloads move together.

## 7. Non-Goals

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
