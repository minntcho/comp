# Internal Execution Design Map

Status: planning-map
Owner: compiler
Can block PRs: no

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

## Design Lens

This map should describe internal execution logic with three questions:

```text
Requirement
  What must be true before material can advance?

Satisfaction mechanism
  What kind of system-recognized material can satisfy that requirement?

Invalid satisfier
  What may look persuasive but must not count as satisfying the requirement?
```

This lens keeps the discussion centered on execution behavior instead of file
layout or implementation mechanics. For example, a candidate value is not
validated merely because it exists in source text, appears in a fixture, or is
recommended by a model. It must satisfy the requirement recognized by the
relevant execution capability.

## Current Design Frame

The current system mostly behaves as a closed-schema validation path: accepted
fields, allowed units, evidence grounding, obligations, commit readiness,
receipts, and replay determine whether a candidate can become public output.

In a closed-schema path, the compiler expects a selected field set and unit set
before claim validation. If a candidate uses a field outside that selected set,
the system treats it as material that cannot yet be checked by the current
contract.

The design discussion raised a different capability: incoming source or
extractor output may contain attributes whose meaning is not already fixed by
the selected compiler-checkable field set. That is not just a small procedural
variation. A system that discovers or recommends attribute meaning begins from a
different execution posture than a system that validates only against a
preselected schema.

This map therefore keeps two ideas separate:

```text
Closed validation
  The selected schema/profile already exists. Candidate claims are checked
  against it.

Pre-validation attribute handling
  Incoming attributes may need to be interpreted, mapped, proposed, rejected, or
  held for decision before ordinary claim validation can run.
```

This does not mean that recommendation, extraction, scenario fixtures, or user
selection become public-output authority. The intended boundary remains:
pre-validation capabilities may help shape what is submitted for validation;
compiler, commit, receipt, and replay capabilities determine whether anything is
trusted enough for public projection.

## Captured Design Notes

### Attribute handling is not claim validation

The discussion started from the current closed-schema behavior: a claim field is
checked against the selected field set. If the field is not known to the current
compiler contract, the claim cannot be validated as an ordinary checked claim.

That behavior is appropriate for the authority path, but it is not enough to
cover every upstream input mode. When source or extractor output contains fields
such as:

```text
fuel_volume_liters = 1200
plant = "A"
month = "2026-01"
fuel = "diesel"
```

there are at least two different execution postures:

```text
Closed validation posture
  These fields must already be known or mapped before validation.

Discovery/recommendation posture
  These fields may be candidates for interpretation before validation.
```

The important design point is that attribute handling should not quietly loosen
claim validation. It should decide what can be submitted into validation, what
needs a decision, and what should stay out of the validation path.

### Recommendation may precede selection, but cannot replace selection

A recommendation capability may suggest that a source attribute resembles an
existing compiler-checkable field. For example:

```text
fuel_volume_liters may correspond to amount
plant may correspond to site
month may correspond to period
fuel may correspond to activity_type
```

That recommendation is useful only as pre-validation material. It does not make
the field checked, does not add the field to the active schema by itself, and
does not authorize a public row. Some selection mechanism still needs to decide
what is active for validation.

The open question is not whether every recommendation should be accepted. The
useful design question is what kind of selected or approved material is required
before the compiler treats the result as part of the active validation contract.

### Attribute decisions should be separable from the compiler authority path

The discussion favored separating attribute decision logic from core claim
validation so the compiler does not become a collection of ad hoc field-name
special cases.

A future capability may support outcomes such as:

```text
accept as already canonical
map from source-specific attribute to canonical field
propose as a possible new field
reject as irrelevant or unsafe for validation
hold for user, policy, profile, or later decision
```

These are conceptual outcomes, not committed API names. The point is that each
outcome changes what is submitted to validation or held back from it. None of
these outcomes is public-output authority.

### Public authority remains downstream of validation, commit, receipt, and replay

A flexible attribute layer would make the system more adaptable, but it must not
change the authority boundary. The public-output path still requires validated
material, commit readiness, designated receipt authority, and replayable
artifact support.

The design should keep the following distinction visible:

```text
A recommendation can propose meaning.
A selection can decide what to validate.
A compiler can validate claims against the selected contract.
A commit path can package accepted material.
A receipt can authorize projection.
Replay can verify that the public row remains explainable.
```

Skipping any of those distinctions would make the system easier to use but less
trustworthy.

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

Possible requirement framing:

```text
Requirement
  Compiler-submitted claim fields should be interpretable under the selected
  validation contract.

Satisfaction mechanism
  Some attribute-handling capability resolves, maps, proposes, rejects, or holds
  incoming attributes before claim validation.

Invalid satisfier
  A source attribute name, model recommendation, or fixture field should not by
  itself become an active compiler field.
```

The goal is to keep field interpretation flexible without letting unknown or
recommended fields bypass validation.

### Evidence Grounding

The system may need a way to decide whether a candidate claim is backed by
usable source evidence.

This area covers whether a claim has an evidence witness, whether that witness
points to the same field, whether the witness is grounded in a source or span,
and whether the evidence can later be represented in replayable material.

Possible requirement framing:

```text
Requirement
  A claim should be backed by usable evidence before it can become checked
  material.

Satisfaction mechanism
  The claim has a witness that matches the field and is grounded in source/span
  material that can later be represented for replay.

Invalid satisfier
  A witness identifier alone, a plausible source name, or a fixture expectation
  should not satisfy evidence grounding.
```

### Claim Validation

The system may need a way to validate candidate claims against the currently
selected field, unit, rule, and profile expectations.

This area covers closed validation behavior after any pre-validation attribute
handling has finished. It is where candidate material should become checked,
failed, unknown, unchecked, or obligation-bearing.

Possible requirement framing:

```text
Requirement
  Candidate material should be classified under the selected validation
  contract.

Satisfaction mechanism
  The compiler evaluates field coverage, values, witnesses, units, and other
  selected rules, then records the result as checked, failed, unknown,
  unchecked, or requirement-bearing material.

Invalid satisfier
  LLM confidence, source plausibility, downstream scenario shape, or expected
  output should not replace compiler validation.
```

### Requirement Handling

The system may need a way to represent unresolved requirements and determine
what kind of material can satisfy them.

This area covers obligations, resolver artifacts, semantic judgments, reference
lookups, missing evidence, review requirements, and other unresolved conditions.
It should preserve the difference between proposing material and satisfying a
compiler-recognized requirement.

Possible requirement framing:

```text
Requirement
  Unresolved validation conditions should stay visible until a recognized
  satisfaction mechanism closes them.

Satisfaction mechanism
  The system records structured requirements and accepts only matching resolver,
  evidence, judgment, reference, or review material according to the relevant
  rule.

Invalid satisfier
  Warning text, manual notes, or resolver output that does not match the
  requirement should not silently close the requirement.
```

### Profile and Schema Selection

The system may need a way to determine which field set, unit set, rules,
rubrics, reference policies, or profile lock are active for a validation run.

This area covers the boundary between flexible discovery or recommendation and
the selected contract used by the compiler. It should avoid treating proposed
schema changes as automatically active.

Possible requirement framing:

```text
Requirement
  Validation should run against a selected contract, not against every possible
  recommendation or discovered attribute.

Satisfaction mechanism
  A profile, schema selection, policy decision, or other selected contract
  determines what is active for the run.

Invalid satisfier
  A proposed field, candidate mapping, or recommendation should not become
  active merely because it exists.
```

### Commit Readiness

The system may need a way to decide when validated material is ready to be
packaged for public-output consideration.

This area covers the transition from a validation report into review or commit
material. It should preserve the difference between an accepted validation state
and public-output authority.

Possible requirement framing:

```text
Requirement
  Accepted validation material should still pass a commit-readiness boundary
  before public-output authorization is considered.

Satisfaction mechanism
  The system builds review or commit material and determines whether it is
  complete under the selected rules.

Invalid satisfier
  A validation report being accepted should not by itself authorize public
  projection.
```

### Public Output Authorization

The system may need a way to ensure that public projection is authorized only
through the designated receipt authority.

This area covers the boundary between review material, governance decisions,
receipt issuance, authorized fields, and public projection. It should prevent
reports, packages, decisions, scenario results, or recommendations from being
mistaken for projection authority.

Possible requirement framing:

```text
Requirement
  Public projection should require designated public-output authority.

Satisfaction mechanism
  A public-output receipt or equivalent designated authority grants projection
  over specific fields.

Invalid satisfier
  A review package, governance decision, accepted report, scenario result, or
  recommendation should not authorize public projection by itself.
```

### Artifact and Replay Support

The system may need a way to preserve the material needed to explain and replay
public output.

This area covers receipt-cited artifact material, artifact envelopes, digest
checks, committed values, dependency fingerprints, source evidence, reference
coverage, and replay verification.

Possible requirement framing:

```text
Requirement
  Public output should remain explainable and replayable from the material cited
  by its authority object.

Satisfaction mechanism
  Receipt-cited material is preserved as replayable artifacts and verified by
  digest, value commitment, dependency fingerprint, and source/reference checks.

Invalid satisfier
  Expected output comparison, fixture existence, or benchmark success should not
  replace replay verification.
```

### Downstream Scenario Validation

The system may need a way to check that larger scenario packs exercise the same
trust path without becoming authority sources.

This area covers prepared scenario bundles, compatibility reports, performance
or query rehearsals, blocked/accepted scenario expectations, and downstream
signals that remain subordinate to compiler, receipt, and replay authority.

Possible requirement framing:

```text
Requirement
  Large downstream scenarios should demonstrate that the trust path survives
  realistic domain or product-shaped inputs.

Satisfaction mechanism
  Scenario packs submit prepared bundles and run the public replay/compatibility
  path without replacing compiler, receipt, or replay authority.

Invalid satisfier
  A downstream domain fixture, expected row, query benchmark, or scenario label
  should not count as public-output authority.
```

## Running Example: Attribute Before Validation

A source or extractor may produce attributes such as:

```text
fuel_volume_liters = 1200
plant = "A"
month = "2026-01"
fuel = "diesel"
```

A closed-schema validation path can only validate this material after the fields
are already part of, or mapped into, the selected validation contract. Without
that, the compiler should not pretend that the attributes are ordinary checked
claims.

A more flexible pre-validation capability may instead treat those attributes as
material to interpret before validation. It might decide that some attributes
map to existing fields, that some need a decision, and that some should be held
back or rejected. After that decision, the compiler still validates the resulting
candidate claims under the selected contract.

The running example should preserve the central boundary:

```text
Attribute handling can shape the validation input.
Claim validation decides whether the shaped input is checked.
Commit and receipt decide whether checked material can authorize public output.
Replay decides whether public output remains explainable.
```

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
