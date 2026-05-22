# Document Governance

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-22
Can block PRs: yes

This document defines how architecture documents gain or lose authority in the
`comp` rebuild. Its goal is to keep docs useful as constraints without letting
old notes outrank the current code.

## Core Rule

Documentation is not all equal.

```text
Some docs can block PRs.
Some docs only map the current implementation.
Some docs point north.
Some docs are historical context.
```

Every architecture document that is used in review should declare its authority
level near the top.

## Metadata And Navigation

Document headers are the metadata source of truth.

```text
Status
Owner
Last checked against code
Can block PRs
```

`docs/index.md` is the navigation source of truth.

The index groups documents for humans, but it must not become a second source
of authority metadata. If the index and a document header disagree, fix the
stale one in the same PR.

## Authority Levels

### Active Contract

Defines invariants, authority boundaries, or package ownership rules.

```text
Can block PRs: yes
```

A PR may be rejected for violating an active contract unless the PR also updates
the contract explicitly and explains why the boundary is changing.

Examples:

```text
document-governance.md
trust-kernel-extension-rings.md
persistence-ledger-boundary.md
```

### Implementation Map

Tracks the current shape of code, test harnesses, or scenario structure.

```text
Can block PRs: limited
```

An implementation map can block a PR when the PR changes the mapped area but
does not update the map. It should not override an active contract.

### North Star

Describes long-term direction and preferred expansion paths.

```text
Can block PRs: limited
```

A north-star document can guide roadmap choices and review questions. It should
not block a small implementation PR by itself unless the PR creates authority
confusion that an active contract also forbids.

### Historical / Exploratory Note

Records prior reasoning, sketches, or migration history.

```text
Can block PRs: no
```

Historical and exploratory notes are useful context. They cannot block PRs by
themselves.

## Required Header

Use this header shape for architecture documents that are expected to influence
review:

```text
Status: active-contract | implementation-map | north-star | historical-note
Owner: trust-kernel | persistence | retrieval | scenario-lab | agent-layer | explanation | docs
Last checked against code: YYYY-MM-DD
Can block PRs: yes | limited | no
```

`Last checked against code` means a human or agent compared the document against
the code shape on that date. It is not a promise that the document will remain
fresh forever.

## Location Rules

Status and location should agree.

After the lifecycle migration, docs/architecture/ root is an entry surface. It
may contain a README, governance entry point, or short routing document; the
governed architecture body should live under the status-specific directories.

```text
active-contract -> docs/architecture/contracts/
implementation-map -> docs/architecture/maps/
north-star -> docs/architecture/north-stars/
historical-note -> docs/archive/architecture/
implementation plan -> docs/archive/plans/
migration history -> docs/archive/migration/
```

The current repository may still contain documents that predate this physical
layout. New documents should follow this layout immediately, and migration PRs
should move obvious existing documents without changing their review meaning.

Implementation plans, execution logs, and temporary PR plans should not be
created under `docs/architecture/`. They may be useful, but they are not active
architecture contracts.

## Smoke Enforcement

Package smoke tests enforce the parts of this policy that can be checked
mechanically:

```text
required header keys
status-to-blocking match
lifecycle location
index listing
```

The scanner checks governed architecture docs in `docs/architecture/` and
`docs/archive/architecture/`. It is intentionally narrow: it prevents authority
metadata drift and plan-log leakage without trying to judge whether a document's
argument is correct.

## Review Checklist

Before adding or promoting a document, answer:

```text
Can this document block a PR?
What kind of PR can it block?
Which existing active contract does it refine?
What stale text would mislead future work?
Where is the implementation map that should change with code?
```

If those questions do not have clear answers, prefer a short section in an
existing document over a new document.

## Demotion Rule

When a document becomes stale, do not leave it with implied authority.

```text
active-contract -> implementation-map
implementation-map -> historical-note
north-star -> historical-note
```

After the lifecycle migration, demotion changes both status and location.
Demotion is not deletion. It preserves useful reasoning while removing review
authority.

## Practical Rule

Good architecture docs do not merely enable work. They prevent unsafe work.

```text
If a document cannot name what it forbids, it is probably a note.
```
