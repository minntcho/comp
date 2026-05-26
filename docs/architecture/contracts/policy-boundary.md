# Policy Boundary

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-26
Can block PRs: yes

This contract defines the security boundary between external material and
compiler-facing validation input.

Policy may shape validation input. Policy may not validate. Policy may not
authorize public projection. Policy may not replace replay.

## Purpose

`comp` can support richer policy assembly without turning policy into authority.
The policy boundary controls how external material is described, which
capabilities may inspect it, which decisions may be made from it, and which
pipeline scopes it may enter before compiler validation.

The boundary exists to prevent unresolved, contextual, recommended, or
high-risk material from silently becoming validation input or public output.

## Boundary Scope

This contract governs the path from external material to validation handoff:

```text
External Material
-> MaterialDescriptor
-> Capability Output
-> PolicyEffect
-> ConflictResolver
-> ScopedGrant + DecisionLedger
-> SelectedValidationContract
-> Compiler Validation
-> PublicOutputReceipt
-> Replay
```

The policy boundary governs material resolution, policy effects, scoped grants,
decision ledgers, and validation handoff.

It does not govern compiler validation, receipt authority, or replay authority.
Those remain separate authority paths.

## Non-Authority Rule

These objects are not validation authority and are not public projection
authority:

```text
PolicyEffect
ScopedGrant
SelectionDecision
DecisionLedger
SelectedValidationContract
```

A `ScopedGrant` is pipeline access, not trust authority.

A scoped grant may allow material to be used for candidate generation, selection
evaluation, validation context, validation handoff, replay support, or audit.
It must not make a claim checked, close a validation requirement, authorize
public projection, or replace a `PublicOutputReceipt`.

## Core Terms

`MaterialDescriptor` describes the material before selection. It may include
field knownness, source state, risk tier, projection sensitivity, evidence
availability, and other policy-facing attributes.

`Capability Output` is output from retrieval, embedding, LLM, reviewer, parser,
or resolver capabilities. Capability output is candidate, recommendation,
context, or evidence-request material. It is not authority.

`PolicyEffect` is the common intermediate representation produced by policies.
Effects may propose, hold, reject, request evidence, restrict scope, require
review, set retention, or request replay material.

`ConflictResolver` combines policy effects into final decisions. It applies
kernel invariants first and profile-specific composition rules second.

`ScopedGrant` records which pipeline scope a subject may enter, under which
basis and conditions. It is not a receipt, validation result, or replay proof.

`DecisionLedger` records policy decisions and their basis so selection,
rejection, hold, and escalation decisions are auditable.

`SelectedValidationContract` is the compiler-facing contract produced after
policy decisions and grants. It selects what may be handed to compiler
validation. It does not validate the selected material.

## Grant Scopes

The initial policy vocabulary may use these scopes:

```text
candidate_generation
selection_evaluation
validation_context
validation_handoff
projection_candidate
replay_support
audit_only
```

`validation_handoff` means the material or decision may be passed to compiler
validation. It does not mean the material is valid.

`projection_candidate` means pre-authority eligibility for later receipt
consideration. It does not authorize public projection. `PublicOutputReceipt`
remains the only public projection authority.

`replay_support` means the material may need to be preserved to verify a
receipt-authorized path later. It does not make replay successful by itself.

## Kernel Invariants

Kernel invariants are non-overridable. Profile-specific policy composition may
extend or specialize behavior, but it must not violate these rules:

```text
No policy output validates a claim.
No scoped grant authorizes public projection.
No embedding or LLM output enters validation_handoff without selection basis.
No selected material becomes public output without PublicOutputReceipt.
No policy assembly may bypass receipt or replay boundaries.
ScopedGrant is not PublicOutputReceipt.
```

The policy boundary may restrict access to later pipeline stages. It may not
promote material across compiler, receipt, or replay authority gates.

## Composition Rules

Policy composition has two layers:

```text
kernel invariant > profile policy > capability recommendation
```

Kernel invariants are fixed by this contract.

Default composition ordering may vary by profile, but it must not violate the
kernel invariants. Useful defaults include:

```text
reject > hold > select > propose
declared contract beats embedding similarity
high-risk hold beats auto-select
manual reviewer approval can promote held candidate
non_public scope blocks projection_candidate regardless of selection
```

Capabilities may recommend. Policies may issue scoped access. Contracts may
select validation material. Compiler gates validate. Receipts alone authorize
public projection. Replay verifies the receipt path.

## Relation To Existing Architecture

`ReferenceOption` remains candidate-only, regardless of retrieval score,
embedding similarity, or LLM recommendation.

`CanonicalReference` remains the deterministic selection output for reference
binding. A policy grant may permit reference-selection evaluation or validation
handoff, but it does not replace the deterministic selector.

`CompilerProfile` may identify the active policy assembly, active retrieval
policies, judge policies, projection policy, or profile lock material. A profile
is a behavior lock, not authority by itself.

`PublicOutputReceipt` remains the only public projection authority. Policy
effects, scoped grants, selected contracts, review recommendations, stored rows,
and replay reports must not replace it.

Replay verifies receipt-cited material. Replay reports explain or reject a
receipt path; they do not authorize projection by themselves.

The profile/schema selection resolution tiers note describes candidate
resolution strategies. This contract defines the authority boundary those
strategies must obey.

## Current Implementation Status

This document defines a boundary contract for upcoming policy work.

Not every term in this document is currently a public Python API. Until
implemented, these terms are architectural contract vocabulary.

The first implementation slice lives in `comp.policy`. It exposes
`MaterialDescriptor` and `PolicyEffect` as pre-validation vocabulary only. It
does not expose `ScopedGrant`, `DecisionLedger`, `SelectedValidationContract`,
receipt builders, projection gates, or replay authority.

Existing `CompilerProfile`, `DomainPack`, `RetrievalQueryPolicy`,
reference-selection, resolver-task, and profile/schema selection-tier surfaces
remain precursor surfaces. They are not the full policy boundary
implementation.

New implementation slices should start small. A first slice should prefer
policy effects, conflict resolution, scoped pipeline grants, decision-ledger
records, and selected validation contracts over broad policy taxonomies.
