# Document Governance

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-20
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

Demotion is not deletion. It preserves useful reasoning while removing review
authority.

## Practical Rule

Good architecture docs do not merely enable work. They prevent unsafe work.

```text
If a document cannot name what it forbids, it is probably a note.
```
