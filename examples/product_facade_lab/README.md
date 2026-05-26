# Product Facade Lab

This example is a comp-backed observation lab, not a production runtime.

It exposes a small product-shaped surface:

```text
submit(input)
publish(run_id)
audit(public_row_id)
```

The lab records an artifact touch log for the canonical fast path. It does not
introduce a native production authority engine, artifact registry, Artifact
Passport schema, or `comp.contracts` extraction.
