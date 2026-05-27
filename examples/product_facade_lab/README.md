# Product Facade Lab

This example is a comp-backed observation lab, not a production runtime.

It exposes a small product-shaped surface:

```text
submit(input)
publish(run_id)
audit(public_row_id)
```

The lab records artifact touch logs for the canonical fast path and policy
preflight path. It does not introduce a native production authority engine,
artifact registry, Artifact Passport schema, or `comp.contracts` extraction.

It currently observes two submit shapes:

```text
canonical fast path
  ProductInput
  -> InterpretationHypothesis
  -> ValidationReport

policy preflight path
  ProductPolicyPreflightInput
  -> MaterialDescriptor / PolicyEffect / PolicyAssembly
  -> DecisionLedger / SelectedValidationContract
  -> ValidationHandoff
  -> ValidationReport
```

The policy preflight path is intentionally comp-backed. It measures ceremony
around pre-validation admission; it does not add a product policy engine or let
policy artifacts authorize public projection.

Product facade response observations currently include product-facing status,
`publishable`, user-facing `required_actions`, `receipt_handle`,
`replayable_now`, `audit_pending`, `replay_status`, `verification_errors`, and
`proof_graph_available`. The touch_log is lab-only diagnostic material; it is not
intended as a production response field.

The lab also observes the boundary between product export material and comp
verification output:

```text
export_verification_input(public_row_id)
  -> validation_summary
  -> public_row
  -> PublicOutputSpec projection shape
  -> receipt_handle
  -> PublicOutputReceipt
  -> optional ReceiptSignature
  -> ArtifactEnvelope set
  -> optional explanation hints
  -> omitted_verification_outputs
  -> product_only_excluded

verify_comp_compatible_input(input)
  -> receipt_authenticity_status
  -> replay_status
  -> verification_errors
  -> ProjectionReplayReport, when verified
```

`CompCompatibleVerificationInput` deliberately omits `ProjectionReplayReport`,
proof graph output, `touch_log`, and product-only workflow state. The product
side exports replayable material; the comp verifier produces replay
verification. When a product export carries `ReceiptSignature` material, comp
verifies issuer authenticity as a separate status; that status does not replace
replay verification.

`export_verification_bundle(...)` and `write_verification_bundle(...)` serialize
that material as `product_facade_verification_bundle.v0` JSON for fixture
observation. The bundle is not a stable wire contract or artifact registry.
`verify_verification_bundle(...)` and `verify_verification_bundle_file(...)`
read that fixture shape and return comp verification output; they do not trust
or import a product-generated replay report.
Do not promote `examples.product_facade_lab.bundle` into `comp`,
`comp.runtime`, or `comp.scenario_contracts` from this lab.
Do not add a product facade console script from this lab.

Checked-in fixture bundles live under `fixtures/`. The lab-only fixture runner
exposes `run_fixture(...)` and `run_all_fixtures(...)` so tests can verify that
stored product-shaped material still replays through comp without constructing a
`ProductFacadeRuntime`. The fixture runner is not a CLI, production verifier, or
stable bundle runner.

`fixtures/conformance_cases.json` is a lab-only case manifest. It lists existing
fixture bundles and their expected `replay_status` and
`receipt_authenticity_status` values. `run_case_manifest(...)` reads that
manifest, and `run_conformance_cases(...)` can run the same case shape from
memory. The manifest is not a product export schema or stable wire contract.

Verification bundle lab summary: the lab has observed export via
`export_verification_bundle(...)`, file persistence via
`write_verification_bundle(...)`, file verification via
`verify_verification_bundle_file(...)`, a canonical fixture that verifies from
stored material, a missing artifact fixture that blocks replay, and a
signed bundle authenticity observation that reports receipt authenticity separately
from replay.
This is not a product runtime CLI.
It is not a scenario/conformance runner, and not promotion to a stable wire
contract, stable key registry contract, production cryptography integration,
artifact registry, or native production authority engine.
Product replay reports remain comp verification output.

`compare_touch_logs` can compare two logs from the same operation, such as
canonical `submit` and policy preflight `submit`. The comparison is an
observation summary for spotting ceremony deltas; it is not a lifecycle
contract, artifact registry, or Artifact Passport.
