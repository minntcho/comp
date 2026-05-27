# Product Facade Conformance Runner Map

Status: implementation-map
Owner: scenario-lab
Last checked against code: 2026-05-27
Can block PRs: limited

This map positions the next layer after the product facade verification-bundle
observations.

This map is a runner-direction map, not a runner contract. It does not define a
CLI, stable wire contract, product runtime, native authority engine, or
production cryptography integration.

## Current Position

The current product facade lab is an observation instrument under
`examples/product_facade_lab`.

```text
product facade lab
  submit / publish / audit surface
  artifact touch logs
  verification bundle export/write/verify helpers
  checked-in bundle fixtures
  optional ReceiptSignature authenticity observation

fixture runner
  run_fixture(...)
  run_all_fixtures(...)
  compact conformance results
  no CLI surface

scenario-style conformance runner
  next possible layer
  not implemented by the current lab
```

The current fixture runner proves that comp can read stored product-shaped
material and produce verification output without constructing a
`ProductFacadeRuntime`. It does not yet prove that a downstream product app has
a stable export contract.

## Layer Boundaries

```text
Production App
  owns importers, OCR, UI, supplier workflow, product database rows,
  product policy choices, and product-facing language.

Comp-Compatible Verification Input
  carries validation summary, public row, PublicOutputSpec shape,
  PublicOutputReceipt, optional ReceiptSignature, ArtifactEnvelope material,
  and omitted verification output markers.

Lab Fixture Runner
  reads checked-in lab fixture bundles.
  returns compact conformance results for tests.
  must remain lab-only until promotion criteria are met.

Scenario-Style Conformance Runner
  would run named product-shaped cases across fixture directories.
  would compare expected verified/blocked/authenticity outcomes.
  would still be an observation harness before stable export promotion.

comp verifier
  produces replay_status, receipt_authenticity_status, verification_errors,
  and ProjectionReplayReport when verified.
  does not trust product-generated replay reports.
```

The authority direction is one-way: product-shaped material is emitted or
stored, then comp verifies it. The runner does not mint receipts, repair missing
artifacts, or treat product replay reports as authority.

## Promotion Path

```text
Fixture runner -> scenario-style conformance runner
  allowed when multiple fixture cases need shared execution and reporting.
  still not a CLI, stable bundle schema, or product runtime.

Scenario-style runner -> shared behavioral contract
  allowed when a downstream or product-shaped exporter can emit comparable
  material without importing the lab runtime.

Shared behavioral contract -> stable export contract
  requires a separate active-contract PR after real consumers expose repeated
  schema pressure and the lifecycle boundary remains intact.
```

Promotion must preserve the split between projection authority, replay
verification, receipt authenticity, and product shell state.

## Non-Promotions

This direction does not promote:

```text
not a CLI
not a stable wire contract
not a product runtime
not a native authority engine
not production cryptography integration
not a comp.runtime workflow shell
not a product-generated replay report authority
```

## First PR Boundary

The first PR on this axis should be a map or test guard only.

```text
No new command surface.
No new bundle schema.
No movement into `comp.runtime`.
No trust in product-generated replay reports.
```

After that, a small scenario-style runner may be considered only if it consumes
existing fixture material and keeps all verification output produced by comp.
