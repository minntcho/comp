# Artifact Lifecycle Boundary

Status: active-contract
Owner: trust-kernel
Last checked against code: 2026-05-27
Can block PRs: yes

This contract defines the current state-transition artifact requirements
grounded in the first product facade lab observations.

This is not an artifact registry.
This is not an Artifact Passport schema.
This does not extract `comp.contracts`.
This does not define a native production runtime, product database shape,
export bundle format, or product workflow shell.

The goal is narrower: identify which artifacts are required for current
trust-state transitions, and which artifacts must not be treated as universal
requirements, authority sources, or product-owned state.

## State Transition Requirements

Compact summary:

- canonical submit -> validation: `InterpretationHypothesis`, `ValidationReport`.
- policy preflight submit -> validation: `MaterialDescriptor`, `PolicyEffect`, `PolicyAssembly`, `DecisionLedger`, `SelectedValidationContract`, `ValidationHandoff`, `InterpretationHypothesis`, `ValidationReport`.
- validated -> published: `ValidationReport`, `ReviewPackage`, `ReviewDecision`, `PublicOutputReceipt`, `PublicOutputSpec`.
- published -> replayable/auditable: `ArtifactEnvelope`, `ProjectionReplayReport`.
- replayable/auditable -> explainable: `ProofGraph` is optional and non-authoritative.

### canonical submit -> validation

Synchronous requirements:

```text
InterpretationHypothesis
ValidationReport
```

Canonical submit may skip policy preflight only when the input already has the
minimum compiler-facing evidence shape. It must not skip compiler validation.

### policy preflight submit -> validation

Synchronous requirements:

```text
MaterialDescriptor
PolicyEffect
PolicyAssembly
DecisionLedger
SelectedValidationContract
ValidationHandoff
InterpretationHypothesis
ValidationReport
```

These artifacts shape validation admission for raw-ish external material. They
do not validate claims, authorize projection, or replace receipt replay.

### validated -> published

Synchronous requirements:

```text
ValidationReport
ReviewPackage
ReviewDecision
PublicOutputReceipt
PublicOutputSpec
```

`PublicOutputReceipt` is the projection authority. Policy selection,
validation handoff, replay reports, and explanation views must not be treated
as substitutes for receipt-gated projection.

### published -> replayable/auditable

Synchronous requirements when replayable/auditable state is claimed:

```text
ArtifactEnvelope
ProjectionReplayReport
```

`ArtifactEnvelope` material may be deferred from the publish path when the
runtime is only publishing and is not yet claiming replayable state. Once the
system claims replayable or auditable state, receipt-cited envelope material and
successful replay are required.

### replayable/auditable -> explainable

Optional, non-authoritative material:

```text
ProofGraph
field explanation
rendered view
```

`ProofGraph` is optional and non-authoritative. Explanation may inspect replay
results and artifact references, but it must not authorize projection, repair
missing replay material, or replace receipt verification.

## Non-Requirements

`DecisionLedger` is not required to publish canonical fast-path output.
Policy artifacts must not authorize public projection.
`ArtifactEnvelope` is not publish-path synchronous unless replayable state is claimed at publish time.
`ProofGraph` is not required for replay.
Product-only state must stay outside `comp` artifacts.

Examples of product-only state include importer state, OCR intermediates, UI
action logs, supplier workflow state, and customer-specific product database
rows. Those may be useful to a product runtime, but they are not `comp`
authority artifacts.

## Review Rules

Changes that alter these state-transition requirements must update this
contract and its smoke coverage in the same PR.

Reviewers should reject changes that:

```text
make policy artifacts projection authority
require DecisionLedger for canonical publish
require ArtifactEnvelope before publish when replayable state is not claimed
make ProofGraph mandatory for replay
move product workflow state into comp artifacts
claim lifecycle finality through an artifact registry or passport schema here
```

This contract may later inform an artifact registry or wire contract. That
promotion requires a separate PR with its own tests and migration rationale.
