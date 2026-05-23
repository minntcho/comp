# Internal Execution Design Map

Status: implementation-map
Owner: trust-kernel
Last checked against code: 2026-05-23
Can block PRs: limited

This document is a top-level map for discussing `comp` internal execution
capabilities before they become implementation work, API contracts, or PR-sized
changes.

It exists to preserve design intent while the execution pipeline is still being
worked through. It should record what capabilities the system may need, why they
matter, and what kinds of decisions must eventually be made. It must not freeze
API names, module layout, implementation order, subdocument structure, or final
algorithms before the underlying logic is mature.

## Purpose

The purpose of this map is to support step-by-step internal execution design.
For each functional area, future design notes may ask:

```text
What capability is needed?
What system requirement does it serve?
What kind of mechanism could satisfy that requirement?
What should not count as satisfying it?
When is the idea concrete enough to become a contract, implementation plan, or PR?
```

This map does not require every area to become a separate document. A focused
contract or implementation note should be created only when a specific area has
enough pressure from code, tests, downstream use, or authority-boundary risk to
justify it.

## Current Design Frame

The current system mostly behaves as a closed-schema validation path: accepted
fields, allowed units, evidence grounding, obligations, commit readiness,
receipts, and replay determine whether a candidate can become public output.

Future capabilities may require a more flexible pre-validation layer. For
example, source or extractor output may contain attributes that do not yet match
the current compiler-checkable field set. Those attributes might need to be
accepted, mapped, proposed, rejected, or held for a decision before ordinary
claim validation runs.

This does not mean that recommendation, extraction, scenario fixtures, or user
selection become public-output authority. The intended boundary remains:
pre-validation capabilities may help shape what is submitted for validation;
compiler, commit, receipt, and replay capabilities determine whether anything is
trusted enough for public projection.

## Functional Areas

### Attribute Handling

The system may need a way to decide how source or extracted attribute names
relate to compiler-checkable fields.

This area covers questions such as:

```text
Can an incoming attribute be treated as an existing canonical field?
Should it be mapped from a source-specific name to a canonical name?
Should it be proposed as a new field candidate?
Should it be rejected as irrelevant or unsafe for validation?
Should it wait for a user, policy, profile, or later process to decide?
```

The goal is to keep field interpretation flexible without letting unknown or
recommended fields bypass validation.

### Evidence Grounding

The system may need a way to decide whether a candidate claim is backed by
usable source evidence.

This area covers whether a claim has an evidence witness, whether that witness
points to the same field, whether the witness is grounded in a source or span,
and whether the evidence can later be represented in replayable material.

### Claim Validation

The system may need a way to validate candidate claims against the currently
selected field, unit, rule, and profile expectations.

This area covers closed validation behavior after any pre-validation attribute
handling has finished. It is where candidate material should become checked,
failed, unknown, unchecked, or obligation-bearing.

### Requirement Handling

The system may need a way to represent unresolved requirements and determine
what kind of material can satisfy them.

This area covers obligations, resolver artifacts, semantic judgments, reference
lookups, missing evidence, review requirements, and other unresolved conditions.
It should preserve the difference between proposing material and satisfying a
compiler-recognized requirement.

### Profile and Schema Selection

The system may need a way to determine which field set, unit set, rules,
rubrics, reference policies, or profile lock are active for a validation run.

This area covers the boundary between flexible discovery or recommendation and
the selected contract used by the compiler. It should avoid treating proposed
schema changes as automatically active.

### Commit Readiness

The system may need a way to decide when validated material is ready to be
packaged for public-output consideration.

This area covers the transition from a validation report into review or commit
material. It should preserve the difference between an accepted validation state
and public-output authority.

### Public Output Authorization

The system may need a way to ensure that public projection is authorized only
through the designated receipt authority.

This area covers the boundary between review material, governance decisions,
receipt issuance, authorized fields, and public projection. It should prevent
reports, packages, decisions, scenario results, or recommendations from being
mistaken for projection authority.

### Artifact and Replay Support

The system may need a way to preserve the material needed to explain and replay
public output.

This area covers receipt-cited artifact material, artifact envelopes, digest
checks, committed values, dependency fingerprints, source evidence, reference
coverage, and replay verification.

### Downstream Scenario Validation

The system may need a way to check that larger scenario packs exercise the same
trust path without becoming authority sources.

This area covers prepared scenario bundles, compatibility reports, performance
or query rehearsals, blocked/accepted scenario expectations, and downstream
signals that remain subordinate to compiler, receipt, and replay authority.

## Non-Goals

This map does not prescribe:

```text
API names
class names
module names
implementation order
pipeline order
subdocument names
folder layout
test layout
migration order
specific algorithms
```

Those details should be introduced only when a functional area is concrete
enough to justify a focused design note, contract document, implementation plan,
or PR.

## Promotion Rule

A functional area may be promoted out of this map when at least one of these is
true:

```text
The logic is implemented or about to be implemented.
Multiple modules need the same rule.
A downstream pack must rely on the behavior.
A test needs a named contract to protect the behavior.
A wrong interpretation could leak authority or bypass validation.
The design has become too large to keep as a short map entry.
```

Until then, this document should stay lightweight and should avoid pretending
that unresolved design questions are already settled.
