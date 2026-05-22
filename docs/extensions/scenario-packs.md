# External Scenario Packs

Status: planning
Owner: scenario-lab
Can block PRs: no

`comp` keeps a minimal set of internal scenarios that prove kernel contracts.
Large domain, product, platform, importer, UI, and supplier workflow scenarios
belong in downstream scenario-pack repositories.

The first downstream repository is active:

```text
https://github.com/minntcho/comp-scenario-packs
```

Current checked-in packs:

```text
public_projection_smoke
  active baseline public-surface smoke

l_energy_pcf_governance
  seeded large-domain pack in parallel validation for l_energy_pcf_governance.v1

l_energy_alpha_invalid_allocation_rfi
  seeded blocked/no-projection pack in parallel validation for l_energy.alpha_invalid_allocation_rfi.v1

l_energy_alpha_physical_allocation_correction
  seeded accepted/projection pack in parallel validation for l_energy.alpha_physical_allocation_correction.v1
```

## Boundary

```text
comp
  owns authority contracts
  owns receipts
  owns projection gates
  owns replay validation
  owns minimal kernel e2e scenarios

external scenario packs
  own large domain workflows
  own product/platform fixtures
  own importers and UI/viewer flows
  consume comp through public APIs
  report compatibility and regression signals
```

External scenario packs are compatibility signals, not authority sources.

A downstream pack may submit artifacts, source refs, resolver outputs, fixtures,
expected contracts, and viewer payloads. The compiler still decides whether
obligations are discharged, whether references are canonical, whether derived
claims remain non-public, whether receipts can be minted, and whether public
projection is authorized.

## What Stays Inside Comp

Internal scenarios should stay small and should prove `comp` kernel invariants.

Examples:

```text
raw_claim_hypothesis_gate
raw_claim_acceptance
raw_claim_conflict
raw_claim_conflict_resolution
tiny_pcf
canonical_working_loop
minimal receipt/projection/replay cases
```

An internal scenario belongs in `comp` when a failure indicates a likely kernel
contract regression.

The internal registry exposes residency metadata:

```text
core-kernel
  internal authority-kernel regression scenario

downstream-candidate
  currently internal scenario that should move once a downstream pack owns it
```

This metadata is not a runtime authority source. It is a maintenance signal for
reviewing whether a scenario still belongs in the `comp` repo.

`downstream-candidate` does not mean immediate deletion. Candidate scenarios
should move through this sequence:

```text
copy/reconstruct -> external run -> parallel validation -> internal shrink/remove
```

Until the downstream pack can run the same trust meaning through public `comp`
APIs, the internal scenario remains as regression coverage.

## What Moves Downstream

Large scenarios should move to downstream scenario-pack repositories when they
primarily test domain or product behavior.

Examples:

```text
full L-Energy supplier workflow
synthetic PCF smoke/anomaly/resolution scenarios
large generated datasets
messy source adapter rehearsals
projection query benchmarks
replay performance benchmarks
migration rehearsal cases
agent-produced candidate ingestion tests
platform YAML import
RFI workflow engine
external certificate verification
UI/viewer e2e
large multi-actor orchestration
real reference database integration
product-specific persistence flows
```

A downstream scenario belongs outside `comp` when a failure is more likely to
indicate a domain pack, platform, importer, UI, or workflow regression.

The first external run should stay smaller than the large domain packs. Start
with `public_projection_smoke`, because it proves a downstream repository can
install `comp`, use prepared `RuntimeCase` and `ArtifactEnvelope` files, run the
public scenario bridge, and emit a report without importing `tests.*`.

## Dependency Direction

Downstream repositories consume `comp`.

Before `comp` v1.0, downstream repositories may install `comp` from a Git ref:

```text
comp @ git+https://github.com/minntcho/comp@main
```

After `comp` v1.0, downstream repositories should prefer version ranges:

```text
comp>=1.0,<2.0
```

`comp` must not require downstream repositories to pass its own test suite.

Avoid:

```text
comp tests cloning downstream repositories
git submodules for scenario packs
production imports from downstream scenario code
mandatory PR gates against large downstream scenarios before v1.0
```

Prefer:

```text
documentation links
a downstream registry
manual downstream runs
nightly downstream runs
release-candidate downstream runs
```

## Prepared Bundle Contract

Downstream packs should prepare trust inputs before invoking `comp`:

```text
raw domain/product data
  -> downstream pre-trust adapter
  -> RuntimeCase JSON + ArtifactEnvelope JSONL
  -> comp scenario run
```

Use the public scenario contract helpers:

```python
from comp.scenario_contracts import write_artifact_envelopes, write_runtime_case
```

Do not import `tests.*` or backend-specific JSON codecs from a downstream pack.
See `docs/examples/scenario_contracts/README.md` for the minimal prepared bundle
shape.

See `docs/examples/scenario_pack_repo/README.md` for a copyable downstream repo
skeleton with `pyproject.toml` and a GitHub Actions scenario-contract workflow.

## Review Rule

Before adding a large scenario to `comp`, ask:

```text
If this scenario fails, is the likely bug in comp's authority kernel?
```

If yes, keep it internal and small.

If no, place it in a downstream scenario pack.
