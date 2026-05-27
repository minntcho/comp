# Receipt Authenticity Boundary

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-27
Can block PRs: yes

This contract defines where issuer and signature semantics belong around
`PublicOutputReceipt`.

It does not add a cryptography dependency.
It does not define a stable external wire format.
It does not make product exports authoritative.
It does not change replay into projection authority.

The goal is narrower: prepare the issuer/signature model without confusing
three separate checks that must stay separate.

```text
PublicOutputReceipt is projection authority.
ReceiptSignature is issuer authenticity.
ProjectionReplayReport is replay verification output.
```

## Core Rule

`PublicOutputReceipt` remains the only public projection authority.

A future signature layer can attest that a receipt body came from a known
issuer and has not been changed since signing. That authenticity check is
important, but it is not a second projection gate.

Replay remains separate. Replay checks that the public row and receipt-cited
artifact material still match the receipt. A valid signature does not prove
that replay material is complete. A successful replay does not prove the
receipt came from a known issuer.

The boundary is:

```text
receipt authorizes projection
signature verifies receipt issuer authenticity
replay verifies receipt-cited material
explanation renders replayable context
```

## Receipt Authenticity Concepts

The issuer/signature layer should use explicit concepts when it is implemented:

```text
ReceiptIssuer
  issuer_id
  key_id
  algorithm identifier

ReceiptSignature
  issuer_id
  key_id
  algorithm identifier
  signed_body_digest
  signature value

ReceiptVerificationResult
  status
  issuer_id
  key_id
  signed_body_digest
  errors
```

These names are boundary vocabulary until the code slice promotes them into a
public API. They reserve the meaning of the layer; they do not require a real
crypto library in the first implementation PR.

## Signed Body

The signed body must be the canonical receipt authority body, not a product
wrapper and not a replay report.

The signed body should cover:

```text
receipt identity
public_row_id
projection_id
authorized_fields
barrier_snapshot
PublicOutputReceiptCitations
projection value commitments
dependency fingerprints
```

The signed body must not include:

```text
ProjectionReplayReport
ReceiptProofGraph
field explanations
rendered views
product export bundle wrapper
product UI state
product database rows
materialized public row
```

The materialized public row is verified against the receipt by the projection
gate and replay path. It is not the thing that defines receipt authenticity.

## Verification API Direction

The verification API should make authenticity status explicit instead of
returning a bare boolean.

Expected statuses:

```text
verified
unsigned_legacy
unknown_issuer
invalid_signature
unsupported_algorithm
malformed_signature
```

`verify_public_output_receipt(receipt, key_registry)` is the intended shape,
but the first code slice may use a wrapper or result type if that keeps legacy
receipts compatible. The API must verify receipt authenticity only. It must not
call `build_public_output(...)`, run replay, or inspect product bundle state.

## Legacy Receipt Policy

Unsigned legacy receipts remain replayable.

Older receipt bodies without issuer/signature material must continue to round
trip through persistence and replay unless their receipt-cited material fails
normal replay checks. Authenticity verification should report them as
`unsigned_legacy`, not as `invalid_signature`.

Strict deployments may later reject unsigned legacy receipts at their product
or policy boundary, but that is a deployment rule. The trust kernel must keep
the distinction visible:

```text
unsigned legacy receipt
  no issuer authenticity claim
  may still authorize projection under legacy compatibility
  may still replay if cited material is present and valid
```

## Product Export Boundary

Product exports may carry replayable material, but comp produces replay verification output.

A product app may export:

```text
public row
PublicOutputReceipt
receipt signature material, when available
ArtifactEnvelope set
optional explanation hints
```

The product app must not ask `comp` to trust a product-produced replay result
as authority. `comp` can read exported replayable material and produce its own
`ProjectionReplayReport`.

Reviewers should reject changes that:

```text
treat a product replay report as comp verification
sign a product bundle wrapper instead of the receipt authority body
make a valid signature replace replay
make a successful replay replace issuer authenticity verification
make ReceiptSignature projection authority
block all legacy replay only because a receipt is unsigned
```

## Migration And Test Expectations

The code slice that implements this contract should add tests for:

```text
old unsigned receipt body still round-trips
old unsigned receipt can still replay when artifacts are valid
unsigned authenticity verification returns unsigned_legacy
valid signed receipt returns verified
unknown issuer returns unknown_issuer
changed receipt body returns invalid_signature
replay failure remains separate from signature failure
```

Real cryptographic verification can arrive after the contract shape exists. The
first implementation may use a test verifier or key-registry protocol, but it
must keep the signed body and status model compatible with this boundary.
