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
  conformance_cases.json
  run_case_manifest(...)
  run_conformance_cases(...)
  run_case_manifest_summary(...)
  summarize_conformance_results(...)
  VerificationBundleSuiteResult
  signed_verification_bundle.json
  lab-only case manifest
  not a product export schema
```

The current fixture runner proves that comp can read stored product-shaped
material and produce verification output without constructing a
`ProductFacadeRuntime`. It does not yet prove that a downstream product app has
a stable export contract.

The lab-only case manifest is the first step toward a scenario-style runner: it
lists existing verification bundle fixtures and their expected replay and
receipt-authenticity outcomes. It is not a new bundle schema and must not be
read as a product export format.

`VerificationBundleSuiteResult` summarizes case results into counts, failed
case ids, replay status counts, and receipt-authenticity status counts. The
suite summary remains lab-only reporting; it is not a CLI output format, stable
report schema, or product-facing audit summary.

signed fixture case verifies receipt authenticity when a lab key registry is supplied.
signed fixture case can still replay when key registry material is absent.
That case reports missing authenticity material separately from replay
verification.

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
  runs named product-shaped cases across fixture directories.
  compares expected verified/blocked/authenticity outcomes.
  remains an observation harness before stable export promotion.

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
not a CLI output format
not a stable wire contract
not a product runtime
not a native authority engine
not production cryptography integration
not a comp.runtime workflow shell
not a product-generated replay report authority
```

## First PR Boundary

The first implementation PR on this axis should consume existing fixture
material only.

```text
No new command surface.
No new bundle schema.
No movement into `comp.runtime`.
No trust in product-generated replay reports.
lab-only case manifest
not a product export schema
```

After that, a small scenario-style runner may be considered only if it consumes
existing fixture material and keeps all verification output produced by comp.
