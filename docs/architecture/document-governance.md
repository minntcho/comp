# Document Governance

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-28
Can block PRs: yes

Checked anchors:
- doc: docs/architecture/document-governance.md
- doc: docs/index.md
- test: tests/test_package_smoke.py::test_document_governance_defines_authority_lifecycle_locations
- test: tests/test_doc_lifecycle.py

Freshness triggers:
- governed architecture document header rules change
- docs/index.md architecture routing changes
- tests/test_package_smoke.py governance expectations change
- tests/test_doc_lifecycle.py lifecycle gate behavior changes

Stale-language policy:
- current-status: strict
- future-work: allowed only under explicit future, promotion, open-question, or historical sections

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

## Document Authority Lifecycle

A governed document may be useful as current authority, a current implementation
map, future direction, or historical context.

A document that claims current guidance should carry enough evidence for a
reviewer to know what was checked. A document that describes future work should
isolate that language under an explicit future, promotion, open-question, or
historical section. A historical document must not be cited as current guidance.

This lifecycle is a review aid, not a second authority source over code. Its job
is to keep helpful documents trustworthy without making every small PR perform a
full-document refresh.

## Checked Anchors

`Checked anchors` list the code, tests, or docs that were checked when the
document was last refreshed.

Use this item format:

```text
- code: comp/runtime/validation_handoff.py
- test: tests/test_policy_boundary.py
- test: tests/test_package_smoke.py::test_document_governance_defines_authority_lifecycle_locations
- doc: docs/api/compiler-tool.md
```

Anchors are not proof that the document will stay fresh. They are a review aid
and a future stale-detection hook.

Existing documents may adopt checked anchors incrementally. New or meaningfully
updated governed documents should add them when the document claims current
guidance.

## Freshness Triggers

`Freshness triggers` name the code paths, tests, public surfaces, or external
state changes that should cause a reviewer to re-check the document.

A trigger does not automatically make a PR invalid. It tells reviewers when a
document may need refresh, confirmation, or demotion.

## Refresh Queue

A refresh queue may live under `docs/archive/plans/` when stale candidates are
known but should not interrupt the current PR.

Refresh queue entries cannot block PRs. They are a non-authoritative maintenance
list for follow-up work. A queue entry is not proof that a document is stale and
must not be cited as current guidance.

Each queue item should name the document, the suspected issue, the anchor check
needed before changing it, and the target action: refresh, confirm no drift, or
demote/archive.

The allowed queue outcomes are refresh, confirm no drift, or demote/archive.

## Body Freshness Rules

Status controls how much current-state evidence a document should carry:

```text
active-contract
  states current invariants, prohibitions, authority boundaries, and blocking
  rules. Planning language belongs only in explicit future or promotion sections.

implementation-map
  tracks the current implementation shape, mapped paths, mapped tests, known
  gaps, and promotion paths. Current-state sections should not read like an
  unlanded plan.

north-star
  may discuss direction and candidates. Landed work should move into an
  implemented or current-status section, or into an implementation map.

historical-note
  preserves context. It must not be cited as current guidance.
```

## Document Change Definition of Done

A PR that changes governed architecture meaning should update, or explicitly
confirm no update is needed for:

```text
1. The governed document body.
2. The required header.
3. Checked anchors.
4. Freshness triggers.
5. docs/index.md when document routing changes.
6. Smoke or lifecycle tests when authority rules change.
7. Related API docs or README authority surfaces when public import or
   user-facing guidance changes.
```

A code PR that changes a declared checked anchor or freshness trigger should
either update the governed document, refresh its checked date with an explicit
no-drift note, or explain why the document is no longer current guidance.

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

The scanner checks the root governance entry point, governed architecture docs
in `docs/architecture/contracts/`, `docs/architecture/maps/`,
`docs/architecture/north-stars/`, and historical notes in
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
