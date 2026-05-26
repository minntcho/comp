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
