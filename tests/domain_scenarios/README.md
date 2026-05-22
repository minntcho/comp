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

Start with `canonical_working_loop`, the raw-input harness for new contributors.
It begins with a raw evidence sentence, uses a deterministic extractor stub,
passes through `CompilerTool`, opens a calculation obligation, resolves a
reference search obligation through `ResolverTask`, a profile-active
`RetrievalQueryPolicy`, and the retrieval bridge, turns candidate-only retrieval
results into a canonical binding through deterministic selection, calculates a
derived claim, mints a public-output receipt, and projects only through the
receipt gate.

The smaller scenario `tiny_pcf` is a product-carbon-footprint slice that exercises
reference search, near-miss rejection, canonical binding, calculation trace,
commit preparation, and receipt-gated projection.

The first larger source-referenced pack is `l_energy_pcf_governance`, based on
`minntcho/esg-platform` case `001-l-energy-pcf-governance`. It uses
fixture-derived downstream claims from the platform expected receipt, but routes
the L-Energy own-energy factor through a retrieval-backed slice: calculation
blocked, reference search obligation, `ResolverTask`, `RetrievalQueryPolicy`,
candidate-only embedding stub results with near-miss reference rows,
deterministic reference binding, retry, and receipt-gated projection. This keeps
the case realistic without adding a full PCF workflow engine.

## Testing Philosophy

Domain scenario tests should lock authority boundaries, not implementation shape.
They are pressure tests for the compiler contract, not golden snapshots of a
final LCA, DPP, UI, or reference database schema.

Scenario creation guidance lives in
`docs/architecture/maps/domain-scenario-pack-generation.md`. Treat larger scenarios
as swappable Scenario Pack modules, not hard-coded golden fixtures.

The shared test-support layer now exposes:

```text
ScenarioDefinition
ScenarioContract
SourceRef
ScenarioReferencePack
run_scenario()
assert_scenario_contract()
scenario_result_view()
assert_receipt_trace()
assert_projection_tamper_blocked()
registered_scenarios()
```

New scenarios should enter through explicit registry registration instead of
being auto-discovered from the filesystem.

Strong assertions are encouraged for core invariants:

```text
ReferenceOption remains candidate_only
retrieval_score never authorizes truth
CanonicalReference is required for calculation authority
CalculatedClaim cannot authorize public output
PublicOutputReceipt is required for public output
open obligations prevent receipt issuance
receipt traces binding, formula, calculation, and derived-claim evidence
receipt dependency fingerprints pin replay profile/reference dependencies
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

Use `scenario_result_view()` when a test needs the viewer/export payload. Use
`assert_receipt_trace()` for receipt citation checks, and
`assert_projection_tamper_blocked()` for receipt value-gate negative tests.
That keeps scenario tests focused on the contract instead of repeating receipt
field traversal or projection tamper boilerplate in every pack.

Use `ScenarioReferencePack` when a scenario needs a swappable reference fixture:
it bundles the canonical `ReferenceCatalog`, retrieval resolver/index, and their
fixture version labels so larger domain packs can replace reference data without
rewiring the scenario runner.

## External Scenario Packs

This directory keeps minimal scenarios that prove `comp` kernel contracts.

Large domain/product e2e scenarios should continue in downstream scenario-pack
repositories, starting with:

```text
https://github.com/minntcho/comp-scenario-packs
```

External scenario packs are compatibility signals, not authority sources.

Use this directory for small scenarios where a failure indicates a likely
`comp` authority-kernel regression. Use downstream scenario packs for full
supplier workflows, platform importers, UI/viewer e2e, certificate verification,
large multi-actor orchestration, and product-specific flows.

See:

```text
docs/extensions/scenario-packs.md
docs/extensions/downstream-registry.json
```

## Scenario Residency

The registry exposes residency metadata so internal scenario sprawl is visible
before it becomes package shape.

```text
core-kernel
  small scenarios where failure likely means a comp authority-kernel regression

downstream-candidate
  currently internal scenarios retained until comp-scenario-packs owns them
```

Current core-kernel scenarios include `canonical_working_loop`, `tiny_pcf`,
and the raw-claim boundary scenarios. Current downstream-candidate scenarios
are the `l_energy.*` family, `l_energy_pcf_governance.v1`, and synthetic PCF smoke/anomaly/resolution.

Downstream-candidate is not a removal instruction. Keep the internal scenario
until a downstream pack has copied or reconstructed the same trust meaning, run
it through public `comp` APIs, and passed parallel validation.

## Local Runner

The scenario registry can also be inspected without opening the pytest files:

```bash
python -m tests.domain_scenarios list
```

The list output includes scenario id, residency tier, and title.

Run one scenario as a human-readable trace summary:

```bash
python -m tests.domain_scenarios run canonical_working_loop.raw_text_pcf.v1
```

Run every registered scenario through the same contract assertion path:

```bash
python -m tests.domain_scenarios run-all
```

Use `--json` when a test, viewer, or debugging script needs the existing
`DomainScenarioResult` viewer payload or an aggregate run payload:

```bash
python -m tests.domain_scenarios run l_energy_pcf_governance.v1 --json
python -m tests.domain_scenarios run-all --json
```

When a scenario has a public-output receipt and replayable projection, the JSON
payload includes `proof_graph`. The graph is explanation-only: it is derived after
replay succeeds, hides raw committed values by default, and cannot authorize a
projection.

To inspect that graph visually, render the exported scenario payload:

```bash
python -m tests.domain_scenarios run synthetic_pcf.smoke.v1 --json > scenario.json
comp-receipt-graph render-mermaid --graph scenario.json --output proof-graph.mmd
comp-receipt-graph render-dot --graph scenario.json --output proof-graph.dot
```

The runner is intentionally generic. It only knows about `ScenarioDefinition`,
`registered_scenarios()`, `run_scenario()`, and `DomainScenarioResult`; scenario
packs own their domain fixtures and expected contracts.
