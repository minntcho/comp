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

The first larger source-referenced pack is `l_energy_pcf_governance`, based on
`minntcho/esg-platform` case `001-l-energy-pcf-governance`. It uses
fixture-derived claims from the platform expected receipt to test whether a
realistic PCF governance case can be represented as `comp` authority artifacts
without adding a full PCF workflow engine.

## Testing Philosophy

Domain scenario tests should lock authority boundaries, not implementation shape.
They are pressure tests for the compiler contract, not golden snapshots of a
final LCA, DPP, UI, or reference database schema.

Scenario creation guidance lives in
`docs/architecture/domain-scenario-pack-generation.md`. Treat larger scenarios
as swappable Scenario Pack modules, not hard-coded golden fixtures.

The shared test-support layer now exposes:

```text
ScenarioDefinition
ScenarioContract
SourceRef
run_scenario()
assert_scenario_contract()
registered_scenarios()
```

New scenarios should enter through explicit registry registration instead of
being auto-discovered from the filesystem.

Strong assertions are encouraged for core invariants:

```text
ReferenceCandidate remains candidate_only
retrieval_score never authorizes truth
ReferenceBinding is required for calculation authority
DerivedClaim cannot authorize public projection
CommitReceipt is required for projection
open obligations prevent receipt issuance
receipt traces binding, formula, calculation, and derived-claim evidence
```

Weak assertions are preferred for surfaces that are still exploratory:

```text
exact viewer JSON shape
resolver function names
file or module layout
fixture factor values as real-world PCF truth
final LCA/DPP domain-pack schema
UI viewer layout
the exact function where profile-aware gating is enforced
```

Scenario payloads should stay stable enough for a viewer to explain the run, but
tests should avoid asserting one huge exported JSON blob. Prefer targeted checks
that prove the authority boundary and traceability story still hold.
