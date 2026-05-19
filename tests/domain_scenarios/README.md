# Domain Scenario Lab

Domain scenarios are empirical fixtures for checking whether `comp` can survive
small real-domain flows without giving UI or LLM code authority.

```text
pytest/assertion = verdict
scenario result = trace artifact
UI/viewer = observation
```

Each scenario should keep these pieces close together:

```text
input evidence
domain pack/profile
reference catalog
resolver steps
expected obligations
expected bindings
expected derived claims
expected receipt/projection
```

The first scenario is `tiny_pcf`, a product-carbon-footprint slice that exercises
reference search, near-miss rejection, canonical binding, calculation trace,
commit preparation, and receipt-gated projection.
