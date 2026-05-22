# Scenario Trust Runtime Bridge

Status: north-star
Owner: scenario-lab
Last checked against code: 2026-05-22
Can block PRs: limited

This document sketches the public bridge that external scenario packs should use
when they need to pressure-test `comp` without importing `tests.*` or turning the
trust kernel into a product workflow engine.

It is a direction document for the scenario-runtime bridge. The first
implementation slice is intentionally small and should not be treated as a final
scenario pack API.

The stable boundary is:

```text
External packs prepare canonical or candidate trust inputs.
comp runs those inputs through receipt, replay, projection, and persistence
contracts.
Product ingestion stays outside comp.
```

## 1. Goal

`comp` should stay a small proof and authority kernel. Large domain scenarios,
messy source inputs, operational benchmarks, and product rehearsals should live
outside the core repository.

External packs still need a first-class way to run `comp`. They should not copy
private helpers from `tests/domain_scenarios`, import internal modules, or learn
the shape of current pytest fixtures.

The desired shape is:

```text
comp-scenario-packs
  scenario manifest
  prepared RuntimeCase
  prepared ArtifactEnvelope bundle
  expected invariants
  benchmark budgets
        |
        v
comp public scenario contracts / CLI
        |
        v
narrow TrustRuntime
        |
        v
artifact / receipt / replay / projection / persistence core
```

## 2. Non-Goal: Product Runtime

The bridge must not make `comp` responsible for product ingestion.

These belong outside `comp`:

```text
CSV parsing
email parsing
OCR
LLM extraction
supplier workflow
worker orchestration
UI query simulation
benchmark dataset generation
domain-specific adapter code
```

Those capabilities may exist in downstream products or external scenario packs.
They may prepare inputs for `comp`, but they must not become responsibilities of
the trust kernel.

## 3. Proposed Public Surface

The first public bridge can be small:

```text
comp/scenario_contracts/
  manifest.py
  case.py
  result.py
  invariants.py
  runner.py
  report.py

comp/runtime/
  trust_runtime.py

comp/cli/
  scenario.py
```

The intended user-facing imports are:

```python
from comp.scenario_contracts import ScenarioManifest, RuntimeCase
from comp.scenario_contracts import ScenarioResult, run_scenario
```

The intended CLI shape is:

```bash
comp scenario validate path/to/scenario.yaml
comp scenario run path/to/scenario.yaml --report reports/latest.json
```

`comp scenario run` should execute the trust path only. It should not execute
external pack adapters by default.

## 4. TrustRuntime Scope

`TrustRuntime` should be narrow enough that it cannot grow into a product shell.

Allowed responsibilities:

```text
validate RuntimeCase
record ArtifactEnvelope objects
record CommitReceipt roots
materialize receipt-authorized projection rows
verify materialized projection rows
replay projection rows from receipt-cited artifacts
emit ScenarioResult
```

Out-of-scope responsibilities:

```text
parse raw product files
call LLM providers
run OCR
assign resolver workers
own supplier workflow state
render product UI
decide product query semantics
generate benchmark datasets
```

If a scenario requires raw data preparation, the external pack should run a
pre-trust adapter before invoking `comp`.

## 5. Manifest Modes

The first manifest mode should accept prepared trust inputs:

```yaml
id: esg_energy_mvp
input_mode: canonical_bundle

runtime_case:
  path: prepared/runtime_case.json

artifact_envelopes:
  path: prepared/artifact_envelopes.jsonl

expected:
  invariants:
    - receipt_exists
    - replay_succeeds
    - all_public_rows_have_receipts
    - projection_values_are_committed
    - blocking_hazards_absent

report:
  format: json
```

External packs that start from messy inputs should prepare the bundle in a
separate step:

```bash
python -m packs.esg_energy_mvp.prepare \
  --input raw/ \
  --output prepared/

comp scenario run packs/esg_energy_mvp/scenario.yaml \
  --report reports/esg_energy_mvp.json
```

This keeps extraction and product workflow in the pack while letting `comp`
exercise the trust path through a stable public contract.

## 6. RuntimeCase

`RuntimeCase` should describe trust-relevant inputs, not raw product documents.

Likely fields:

```text
case_id
profile_id
projection_spec
candidate artifacts or canonical artifact refs
receipt request metadata
materialized projection request
```

`RuntimeCase` may reference artifact envelopes by id. It should not depend on
the current `tests.domain_scenarios` dataclasses or fixture helpers.

## 7. Invariants Instead Of Golden Blobs

External packs should assert authority invariants instead of exact exported JSON
snapshots.

Healthy invariants:

```text
receipt_exists
replay_succeeds
all_public_rows_have_receipts
projection_values_are_committed
blocking_hazards_absent
dependency_fingerprints_present
```

Avoid:

```text
exact receipt JSON equality
exact viewer payload equality
module path expectations
helper function name expectations
field order expectations
```

Exact snapshots can freeze implementation shape and create a second source of
truth. Invariants should preserve the authority story while letting projection
reports, views, and helper modules evolve.

## 8. ScenarioResult And Reports

`run_scenario()` should return a stable `ScenarioResult` and optionally write a
JSON report.

Suggested result shape:

```text
ScenarioResult
  scenario_id
  status
  artifact_count
  receipt_count
  public_row_count
  replay_checked_count
  replay_failed_count
  invariant_results
  performance
  report_path
```

Suggested JSON report shape:

```json
{
  "scenario_id": "esg_energy_mvp",
  "status": "passed",
  "counts": {
    "artifacts": 10000,
    "receipts": 1200,
    "public_rows": 5000
  },
  "invariants": [
    {
      "name": "replay_succeeds",
      "status": "passed"
    }
  ],
  "performance": {
    "runtime_sec": 24.3,
    "projection_query_ms": 83,
    "replay_sec": 5.1
  }
}
```

Performance fields are measurements, not authority.

## 9. Import Boundary

External scenario packs must use public `comp` APIs or the public CLI.

Allowed public areas:

```text
comp.scenario_contracts
comp.runtime
comp.persistence public interfaces
comp.compiler_tool public interfaces
comp.judgment public interfaces
```

Forbidden imports:

```text
tests
tests.domain_scenarios
comp.tests
private helper modules
legacy archived runner modules
```

The bridge should eventually be covered by import-boundary smoke tests so a pack
can consume the same public surface that internal smoke scenarios use.

## 10. Internal Smoke Path

At least one internal canonical smoke scenario should use the public bridge.

Bad shape:

```text
internal tests use tests.domain_scenarios helpers
external packs use comp.scenario_contracts
```

Better shape:

```text
internal smoke uses comp.scenario_contracts.run_scenario
external packs use comp.scenario_contracts.run_scenario or comp scenario run
```

This proves the bridge is real and prevents the public API from becoming a
documentation-only facade.

## 11. First Slice

The first implementation slice should avoid benchmarks, raw ingestion, MySQL
query profiling, and schema migration.

Start with:

```text
ScenarioManifest
RuntimeCase
ScenarioResult
InvariantResult
run_scenario
write_report
comp scenario validate
comp scenario run
one internal smoke scenario using the public runner
```

The first invariants should be small:

```text
receipt_exists
replay_succeeds
all_public_rows_have_receipts
projection_values_are_committed
blocking_hazards_absent
```

Once the bridge is stable, external scenario packs can add large domain data,
materialized projection benchmarks, migration rehearsal cases, and agent-produced
candidate tests without loading that material into the core repository.

## 12. Review Checklist

Use this checklist when adding scenario runtime code or external-pack support:

```text
Does the change keep raw product ingestion outside comp?
Does the external pack use public comp APIs or CLI only?
Does the runner accept prepared RuntimeCase or ArtifactEnvelope inputs?
Does TrustRuntime avoid parser, OCR, LLM, UI, and workflow ownership?
Are expected results invariant-based instead of exact JSON blobs?
Does at least one internal smoke scenario exercise the public bridge?
Can reports show performance without making performance data authoritative?
Does any new scenario code avoid importing tests.* from external packages?
```

## 13. Current Implementation Status

The first public bridge slice is implemented:

```text
comp.scenario_contracts
  loads canonical_bundle JSON manifests, prepared RuntimeCase JSON, and
  ArtifactEnvelope JSONL bundles.

comp.runtime.TrustRuntime
  records prepared artifacts and receipts into in-memory stores, replays declared
  projections, evaluates invariant results, and emits ScenarioResult.

comp scenario validate
comp scenario run
  expose the prepared-bundle trust path through a public CLI.
```

Current limits:

```text
YAML manifests require PyYAML if used; JSON manifests work without extra deps.
Only input_mode=canonical_bundle is accepted.
No raw pack adapter execution exists inside comp.
No benchmark runner, MySQL query profiling, or migration rehearsal is included.
```
