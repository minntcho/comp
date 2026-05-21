# External Scenario Packs

Status: planning
Owner: scenario-lab
Can block PRs: no

`comp` keeps a minimal set of internal scenarios that prove kernel contracts.
Large domain, product, platform, importer, UI, and supplier workflow scenarios
belong in downstream scenario-pack repositories.

The first downstream repository is expected to be:

```text
https://github.com/minntcho/comp-scenario-packs
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
synthetic_pcf.smoke
synthetic_pcf.anomaly
minimal receipt/projection/replay cases
```

An internal scenario belongs in `comp` when a failure indicates a likely kernel
contract regression.

## What Moves Downstream

Large scenarios should move to downstream scenario-pack repositories when they
primarily test domain or product behavior.

Examples:

```text
full L-Energy supplier workflow
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

## Review Rule

Before adding a large scenario to `comp`, ask:

```text
If this scenario fails, is the likely bug in comp's authority kernel?
```

If yes, keep it internal and small.

If no, place it in a downstream scenario pack.
