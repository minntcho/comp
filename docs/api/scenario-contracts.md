# Scenario Contracts API Stability

This document classifies the `comp.scenario_contracts` package surface. It is
an API reference, not an architecture authority contract.

The important rule is:

```text
Public scenario bridge contracts accept prepared trust inputs.
Product ingestion stays outside comp.
TrustRuntime replays and checks invariants; it does not become a product shell.
```

The first public bridge accepts only `input_mode='canonical_bundle'`. External
scenario packs prepare a prepared RuntimeCase + ArtifactEnvelope bundle, then
call `load_manifest(...)` and `run_scenario(...)` or the equivalent CLI path.

## Stable public API

`comp.scenario_contracts.__all__ is the stability contract` for this bridge.
Use these names when writing downstream scenario-pack code and public examples:

```python
from comp.scenario_contracts import (
    InvariantResult,
    RuntimeCase,
    RuntimeProjection,
    ScenarioBundleExistsError,
    ScenarioManifest,
    ScenarioManifestError,
    ScenarioResult,
    artifact_envelope_from_mapping,
    artifact_envelope_to_mapping,
    load_artifact_envelopes,
    load_manifest,
    load_runtime_case,
    run_scenario,
    runtime_case_from_mapping,
    runtime_case_to_mapping,
    runtime_projection_to_mapping,
    write_artifact_envelopes,
    write_public_projection_smoke_bundle,
    write_report,
    write_runtime_case,
)
```

Stable scenario-contract names:

```text
InvariantResult
RuntimeCase
RuntimeProjection
ScenarioBundleExistsError
ScenarioManifest
ScenarioManifestError
ScenarioResult
artifact_envelope_from_mapping
artifact_envelope_to_mapping
load_artifact_envelopes
load_manifest
load_runtime_case
run_scenario
runtime_case_from_mapping
runtime_case_to_mapping
runtime_projection_to_mapping
write_artifact_envelopes
write_public_projection_smoke_bundle
write_report
write_runtime_case
```

## Public companion surface

`ArtifactEnvelope is a public companion surface` for scenario contracts. It is
owned by `comp.persistence`, but external packs may import it intentionally when
constructing prepared artifact bundles:

```python
from comp.persistence import ArtifactEnvelope
from comp.scenario_contracts import write_artifact_envelopes
```

Prefer the package-level `comp.persistence` import. Do not import private
implementation modules, `tests.*`, or `tests.domain_scenarios` helpers from a
downstream pack.

## Runtime contract

The trust bridge flow is:

```text
scenario manifest
  -> RuntimeCase JSON
  -> ArtifactEnvelope JSONL
  -> comp.scenario_contracts.run_scenario
  -> TrustRuntime
  -> replay_public_projection
  -> ScenarioResult
```

`RuntimeCase` describes trust-relevant inputs: receipts and projection rows.
`RuntimeProjection` names the projection key, authorized field shape, and row
values that replay will verify. It is not a raw product document model.

`ScenarioManifest` resolves the prepared bundle paths and rejects any input mode
except `input_mode='canonical_bundle'`. New raw-input modes require a separate
contract change because product ingestion, parsers, OCR, LLM orchestration, UI
workflow, and importer behavior stay outside `comp`.

`run_scenario(...)` loads the prepared bundle, executes `TrustRuntime`, writes an
optional JSON report, and returns `ScenarioResult`. A passing scenario result is
a compatibility signal; it is not a new authority root.

## Invariants

The current manifest invariant names are:

```text
receipt_exists
replay_succeeds
all_public_rows_have_receipts
projection_values_are_committed
blocking_hazards_absent
```

Invariant names are public strings because downstream packs place them in
scenario manifests. Unknown invariant names fail the scenario result instead of
being ignored.

`projection_values_are_committed` is checked through the replay path. The
scenario invariant delegates to replay success because `replay_public_projection`
already verifies receipt authorization, value commitments, cited artifact
digests, dependency fingerprints, and source artifact values.

## Authority boundary

External scenario packs may own:

```text
scenario manifests
prepared RuntimeCase files
prepared ArtifactEnvelope JSONL files
domain fixtures
benchmark filters and row presets
compatibility reports
```

External scenario packs must not own:

```text
receipt minting authority
projection authorization
replay replacement logic
canonical reference promotion
private comp implementation imports
comp test-helper imports
```

The dependency direction is downstream-to-`comp`. `comp` exposes this public
bridge so scenario-pack repositories can provide compatibility and regression
signals without becoming authority sources.

## Promotion rule

To change this API:

```text
1. Update comp.scenario_contracts.__all__.
2. Update this document's stable public API list.
3. Update docs/index.md if a new API reference is added.
4. Update tests/test_package_smoke.py so the stability class is machine-checked.
5. Preserve the rule that Product ingestion stays outside comp.
```
