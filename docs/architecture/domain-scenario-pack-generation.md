# Domain Scenario Pack Generation

Status: active guidance for Domain Scenario Lab growth.

This document defines how to add larger domain scenarios without turning them
into hard-coded golden blobs. A scenario is not a one-off test file. It is a
small, swappable Scenario Pack that can be registered, run, inspected, and
replaced as the domain model evolves.

The goal is to let realistic LCA, DPP, PCF, and governance cases pressure-test
`comp` while keeping the compiler core generic.

---

## Core Rule

```text
Scenario Pack = replaceable domain fixture module
pytest/assertion = verdict
ScenarioResult = trace artifact
viewer payload = observation
```

Do not make a scenario pack the source of public authority. A scenario pack
submits inputs, resolver steps, catalogs, and expected contracts. The compiler
still decides whether artifacts discharge obligations, whether bindings are
canonical, whether derived claims remain non-public, and whether a receipt can
authorize projection.

---

## Why Packs Instead Of Golden Fixtures

Large ESG/PCF cases drift. Source systems change, reference factors get revised,
domain packs split, and UI labels move. If a scenario is stored as one huge
expected JSON blob, every small domain edit becomes a brittle test failure.

Scenario packs should instead lock the authority story:

```text
candidate stays candidate_only
binding is required before calculation authority
derived claim is not public output
open obligations block commit
receipt cites the proof artifacts
projection requires receipt authority
```

Scenario packs should avoid locking exploratory shape:

```text
viewer JSON field order
module paths
UI copy
exact resolver helper function names
real-world factor truth
final LCA/DPP schema
```

---

## Minimal Pack Shape

Recommended module layout:

```text
tests/domain_scenarios/
  core.py
  contracts.py
  registry.py

  tiny_pcf/
    scenario.py
    fixtures.py
    expected.py

  l_energy_pcf_governance/
    scenario.py
    fixtures.py
    expected.py
```

The current `tiny_pcf` module predates the registry layer and can be migrated
incrementally. New scenarios should be written as if they are packs, even before
the shared registry exists.

---

## ScenarioDefinition

Each scenario pack should expose a single definition object or equivalent
factory:

```python
SCENARIO = ScenarioDefinition(
    scenario_id="l_energy_pcf_governance.v1",
    title="L-Energy PCF Governance",
    source_refs=(...),
    profile=...,
    reference_catalog=...,
    input_claims=...,
    resolver_plan=...,
    contract=...,
    projection_spec=...,
)
```

The exact Python dataclass does not need to exist before the next implementation
slice. The important contract is conceptual:

```text
ScenarioDefinition
  id and version
  source refs
  profile / domain pack
  reference catalog
  input evidence or checked claims
  resolver plan
  expected contract
  projection spec
```

The scenario module owns domain data. The shared runner owns execution shape.

---

## ScenarioContract

Expected values should be expressed as targeted contracts, not full snapshot
equality:

```python
ScenarioContract(
    must_commit=True,
    required_projection_fields=("total_emission_tco2e", "kgco2e_per_kwh"),
    required_actor_outputs=(...),
    required_receipt_citations=(...),
    required_closed_obligations=(...),
    required_open_obligations=(),
)
```

Strong contract examples:

```text
CommitReceipt exists for the positive path.
open_obligation_ids == ()
hazard_ids == ()
receipt cites expected formula ids.
receipt cites expected derived claim ids.
receipt cites expected calculation trace ids.
ReferenceCandidate.authority == "candidate_only".
DerivedClaim.can_authorize_public_projection is False.
Projection without receipt raises ProjectionBlocked.
```

Weak contract examples:

```text
exact exported viewer JSON equals fixture blob
every audit timeline summary string is byte-for-byte identical
all module filenames are fixed forever
every intermediate helper function name appears in the result
```

Do not assert one huge exported JSON blob. Prefer focused assertions that prove
authority boundaries and traceability.

---

## SourceRef

External product or platform cases should preserve where they came from:

```python
SourceRef(
    repo="minntcho/esg-platform",
    commit="618c44dfcea1ee1e235550776acb78d8f20a7e0c",
    path="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
)
```

Source refs are trace metadata. They are not runtime dependencies. The `comp`
test suite should not need to clone `minntcho/esg-platform` to run.

For the first L-Energy PCF scenario, copy only the minimal values required for
the scenario contract into the pack and keep source refs to the original
platform documents:

```text
docs/e2e/cases/001-l-energy-pcf-governance.md
docs/e2e/dummy-data-mapping-l-energy-pcf.md
tests/e2e/cases/001-l-energy-pcf-governance.yaml
tests/e2e/expected/001-l-energy-pcf-governance.receipt.json
```

---

## Runner And Registry

The runner should be shared:

```text
ScenarioDefinition
-> ScenarioRunner
-> ScenarioResult
-> ContractAssertions
-> optional viewer payload
```

The tests should eventually look like:

```python
@pytest.mark.parametrize("scenario", registered_scenarios())
def test_registered_domain_scenario_contracts(scenario):
    result = run_scenario(scenario)
    assert_contract(result, scenario.contract)
```

`registered_scenarios()` should return explicit scenario modules. Do not auto-load
all installed Python packages or all files under a directory. Scenario activation
should be deliberate, versioned, and reviewable.

---

## L-Energy PCF Governance Pack

The next large scenario should use `minntcho/esg-platform` case
`001-l-energy-pcf-governance` as its source. The first pack should not implement
a full PCF SaaS workflow. It should prove that the platform case can be
represented as `comp` authority artifacts.

Recommended first contract:

```text
case_id = 001-l-energy-pcf-governance
actors:
  l_energy
  alpha_metal
  steel_frame
  c_pack
  carbon_tech
  l_materials

actor outputs:
  l_energy own emission = 1,695 tCO2e
  alpha_metal = 5,306 tCO2e
  steel_frame = 4,750 tCO2e
  c_pack = 10,534 tCO2e
  carbon_tech = 13,390 tCO2e
  l_materials = 174,375 tCO2e

summary:
  total_emission_tco2e = 199,994
  packs = 100,000
  total_energy_gwh = 7.5
  kgco2e_per_pack = 1,999.94
  kgco2e_per_kwh = 26.66
```

The first implementation may use precomputed derived claims from the platform
receipt. That is acceptable if the pack clearly labels them as fixture-derived
claims and still verifies receipt-gated projection.

Non-goals for the first L-Energy pack:

```text
No economic allocation engine.
No RFI workflow engine.
No external certificate verification.
No real LLM quality evaluation.
No YAML parser dependency.
No runtime dependency on esg-platform.
No new production package surface.
```

---

## Review Checklist

Before adding a new scenario pack, answer:

```text
What source refs does this pack preserve?
Which domain values are copied, and why are they minimal?
Which assertions are hard authority boundaries?
Which assertions are intentionally weak?
Does the pack create production authority, or only submit artifacts?
Can the scenario be removed or replaced without changing compiler core?
Can a viewer explain the run without tests asserting the entire viewer payload?
```

If these answers are unclear, document the scenario boundary before adding more
fixtures.

---

## Suggested Work Order

```text
1. Add ScenarioDefinition / ScenarioContract / SourceRef test-support models.
2. Migrate tiny_pcf to the shared registry without changing its behavior.
3. Add l_energy_pcf_governance as a source-referenced scenario pack.
4. Add targeted contract assertions for receipt trace completeness.
5. Add optional static viewer payload only after contracts are stable.
```

The order matters. First create the slot, then plug in the larger scenario.
