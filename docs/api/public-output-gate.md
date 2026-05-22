# Public Output Gate API

This document classifies the top-level `comp` public-output gate surface. It is
an API reference, not an architecture authority contract.

The core rule is:

```text
PublicOutputReceipt is the projection authority.
ValidationReport is not public-output authority.
PublicOutput is a materialized view, not authority.
build_public_output(..., receipt=...) is the gate.
```

The gate exists so public rows cannot be created directly from candidates,
compiler reports, review packages, review decisions, replay reports, or product
UI state. A public projection must pass through a clean
`PublicOutputReceipt`.

## Stable public API

Use these names for public-output examples and package users:

```python
from comp import PublicOutput, PublicOutputBlocked, PublicOutputSpec
from comp import PublicOutputReceipt, PublicOutputReceiptCitations
from comp import PublicOutputValueCommitment, DependencyFingerprint
from comp import build_public_output
```

Stable names:

```text
PublicOutput
PublicOutputBlocked
PublicOutputSpec
PublicOutputReceipt
PublicOutputReceiptCitations
PublicOutputValueCommitment
DependencyFingerprint
build_public_output
```

## Authority Roles

`PublicOutputSpec` defines the projection shape. It names the projection and the
fields the caller wants to materialize. It does not authorize output.

`PublicOutputReceipt` is the projection authority. Its `projection_id`,
`authorized_fields`, citation snapshot, value commitments, and dependency
fingerprints are the authority bundle checked by `build_public_output`.

`PublicOutputReceiptCitations` records the receipt barrier snapshot: governance
status, package completeness, open obligations, hazards, authorized fields,
value commitments, and dependency fingerprints.

`PublicOutputValueCommitment` records the digest for a projected value. Public
projection blocks if the source value does not match the committed digest.

`DependencyFingerprint` records the dependency declarations or source artifacts
that the receipt cites. It supports replay and audit without becoming projection
authority by itself.

`PublicOutput` is the materialized projection view returned by
`build_public_output`. It is derived from a receipt-authorized projection; it is
not an authority root.

## Gate Behavior

`build_public_output(...)` requires a `PublicOutputReceipt`.

It blocks when:

```text
receipt is missing
receipt.projection_id does not match PublicOutputSpec.projection_id
requested output fields are not authorized by the receipt
receipt citations are missing or not clean
open obligations or hazards remain in the receipt snapshot
projected values do not match receipt value commitments
```

It returns only the fields named by `PublicOutputSpec.output_fields`. Extra
fields in the source row are not included in the public output.

## Relationship To Compiler Tool

`comp.compiler_tool` can prepare a commit path and build a
`PublicOutputReceipt` when a report becomes a clean package with a commit
decision. The compiler tool still does not make public output directly.

The first user path is:

```text
InterpretationHypothesis / ClaimCandidate / EvidenceRef
-> CompilerTool
-> ValidationReport
-> prepare_commit
-> PublicOutputReceipt
-> build_public_output
-> PublicOutput
```

The boundary remains:

```text
ValidationReport != public-output authority
ReviewPackage != public-output authority
ReviewDecision != public-output authority
PublicOutputReceipt == public-output authority
```

