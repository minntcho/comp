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
  -> receipt_handle
  -> PublicOutputReceipt
  -> ArtifactEnvelope set
  -> optional explanation hints

verify_comp_compatible_input(input)
  -> replay_status
  -> verification_errors
  -> ProjectionReplayReport, when verified
```

`CompCompatibleVerificationInput` deliberately omits `ProjectionReplayReport`,
proof graph output, `touch_log`, and product-only workflow state. The product
side exports replayable material; the comp verifier produces replay
verification.

`compare_touch_logs` can compare two logs from the same operation, such as
canonical `submit` and policy preflight `submit`. The comparison is an
observation summary for spotting ceremony deltas; it is not a lifecycle
contract, artifact registry, or Artifact Passport.
