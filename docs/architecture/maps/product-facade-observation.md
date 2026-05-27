# Product Facade Observation Map

Status: implementation-map
Owner: trust-kernel
Last checked against code: 2026-05-26
Can block PRs: limited

This map defines the first observation boundary for product-shaped facade work
around `comp`.

This map is observational, not prescriptive. It is not an artifact lifecycle contract,
final product runtime design, native production engine design, or comp-compatible
export format. It defines the first lab boundary for discovering
which `comp` artifacts are actually required, optional, deferred, or unused in
product-shaped flows.

## Purpose

The product facade experiment should measure ceremony before promoting new
contracts.

The goal is to learn which artifacts a user-facing runtime actually needs for:

```text
submit
publish
audit
```

The goal is not to design a new authority engine or to freeze artifact lifecycle
metadata before a product-shaped flow has been exercised.

## Core Rule

`comp` remains a reference trust kernel and conformance oracle.

comp.runtime is not production runtime. It is a reference/conformance runtime surface
that may support scenario execution, replay harnesses, and comp-backed
experiments. It must not become the product workflow shell for importers, UI
state, supplier workflows, product database orchestration, or customer-specific
policy.

Product facade lab work should live outside the `comp` package. It may start as
a sibling experiment, downstream repository, or examples lab, but it must not add
product workflow code under `comp.runtime` or `comp.scenario_contracts`.

## First Lab Shape

The first facade should expose a small product-shaped surface:

```text
submit(input)
publish(run_id)
audit(public_row_id)
```

The first canonical fast-path observation lab lives at
`examples/product_facade_lab`. That lab is comp-backed and remains outside the
packaged `comp` surface.

The first facade must be comp-backed because the goal is ceremony measurement, not independent authority reimplementation.
A native production authority engine
can only be considered after the facade shows which artifacts are required for
product-shaped flows.

The facade should hide most `comp` terms from callers while preserving the
authority chain internally:

```text
product-shaped API
-> comp-backed adapter
-> CompilerTool / prepare_commit / build_public_output / replay
-> artifact touch log
-> later artifact lifecycle boundary
```

## Observation Flows

These flows are initial observation hypotheses, not lifecycle rules.

### canonical_fast_path

Working expectation:

```text
likely sync
  InterpretationHypothesis
  ValidationReport
  PublicOutputReceipt, if publishing

likely omitted
  DecisionLedger
  SelectedValidationContract
  ValidationHandoff
```

Observation goal:

```text
Can canonical input bypass policy preflight without weakening authority?
Which compiler-facing evidence shape is the real minimum?
Which user-facing status maps cleanly to ValidationReport status?
```

Fast path may skip policy preflight only when input is already canonicalized and
has the minimum compiler-facing evidence shape. It must never skip compiler validation,
receipt-gated projection, or replay requirements when those states are claimed.

### policy_preflight_path

Working expectation:

```text
likely sync
  MaterialDescriptor
  PolicyEffect
  SelectedValidationContract
  ValidationHandoff
  ValidationReport

likely audit or deferred
  full DecisionLedger
```

Observation goal:

```text
Which raw-ish inputs require policy admission before validation?
What is the minimum selected contract needed for handoff?
When is DecisionLedger useful audit material instead of submit-path ceremony?
```

The first comp-backed lab must record whether current `comp.policy` assembly
creates `DecisionLedger` synchronously before `SelectedValidationContract`. If it
does, that is an observation about the present reference surface, not a final
claim that every production-shaped preflight path must make the full ledger
synchronous.

### publish_path

Working expectation:

```text
likely sync
  clean ValidationReport
  ReviewPackage
  ReviewDecision
  PublicOutputReceipt
  PublicOutputSpec

under observation
  ArtifactEnvelope materialization timing
```

Observation goal:

```text
When is PublicOutputReceipt synchronously required?
What minimum source row and projection data does build_public_output need?
Can ArtifactEnvelope materialization move to audit/replay without claiming
replayable state too early?
```

### audit_path

Working expectation:

```text
likely sync or deferred
  ArtifactEnvelope set
  ProjectionReplayReport

likely omitted from basic UI
  proof graph
```

Observation goal:

```text
Is replay required immediately after publish, or sufficient as a later audit?
When must ArtifactEnvelope material exist?
Can ProofGraph stay out of the basic product UI path?
```

## Artifact Touch Log

The lab should record an artifact touch log for each operation. The log exists
to support later contract work; it is not itself a stable contract.

Example:

```json
{
  "flow": "canonical_fast_path",
  "operation": "submit",
  "sync_required": [
    "InterpretationHypothesis",
    "ValidationReport"
  ],
  "sync_required_if_publishing": [
    "PublicOutputReceipt"
  ],
  "deferred": [
    "ArtifactEnvelope",
    "ProjectionReplayReport"
  ],
  "not_used": [
    "DecisionLedger",
    "SelectedValidationContract",
    "ValidationHandoff"
  ],
  "product_only": [
    "form_state"
  ],
  "notes": [
    "Canonical input had grounded witnesses and known field/unit coverage."
  ]
}
```

This shape is illustrative. It is not a stable artifact registry or passport schema.
The lab may change the log shape as observations become clearer.

The lab may also produce a touch log comparison observation summary for two
logs with the same operation. That summary exists to identify ceremony deltas
between flows before any lifecycle contract is promoted; it is not an artifact
registry, passport schema, or final product runtime interface.

## Non-Goals

This map deliberately avoids:

```text
no artifact registry yet
no Artifact Passport schema yet
no comp.contracts extraction yet
no native production authority engine yet
no product runtime inside comp package
```

It also avoids promoting `DecisionLedger`, `SelectedValidationContract`,
`ValidationHandoff`, `ArtifactEnvelope`, proof graphs, or replay reports into
universal synchronous requirements before product-shaped observations justify
that move.

## Promotion Criteria

Promotion to Artifact Lifecycle Boundary requires:

```text
1. At least one canonical fast path run with touch log.
2. At least one policy preflight path run with touch log.
3. At least one publish path run showing receipt requirements.
4. At least one audit path run showing replay/artifact requirements.
5. A short comparison identifying sync required artifacts, deferred artifacts,
   omitted ceremony, and product-only state that must stay outside comp.
```

Only after those observations exist should `comp` consider an artifact lifecycle
active contract, artifact registry, Artifact Passport schema, or `comp.contracts`
extraction.

## Review Checklist

Use these questions when reviewing product facade observation work:

```text
Does this PR keep product workflow outside the comp package?
Does it preserve compiler validation, receipt authority, projection gate, and
replay requirements when those states are claimed?
Does it avoid declaring final artifact lifecycle rules?
Does it record artifact touch observations instead of assuming them?
Does it keep comp.runtime as a reference/conformance surface?
Does it avoid creating a native production authority engine?
```
