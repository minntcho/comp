# Scenario Contract Example

This example shows the prepared-bundle shape external scenario packs should
produce before invoking `comp`.

The boundary is intentionally narrow:

```text
raw pack data
  -> pre-trust pack adapter outside comp
  -> prepared RuntimeCase and ArtifactEnvelope bundle
  -> comp scenario run
```

`comp` runs only the trust path. It does not parse raw CSV, email, OCR, LLM, UI,
or supplier workflow inputs.

## Manifest

The first public bridge accepts only `input_mode: canonical_bundle`.

```json
{
  "id": "fixture_public_projection",
  "input_mode": "canonical_bundle",
  "runtime_case": {
    "path": "prepared/runtime_case.json"
  },
  "artifact_envelopes": {
    "path": "prepared/artifact_envelopes.jsonl"
  },
  "expected": {
    "invariants": [
      "receipt_exists",
      "replay_succeeds",
      "all_public_rows_have_receipts",
      "projection_values_are_committed",
      "blocking_hazards_absent"
    ]
  },
  "report": {
    "format": "json",
    "path": "reports/latest.json"
  }
}
```

## Writing A Bundle

External packs should use the public writer helpers instead of importing test
helpers or persistence backend encoders directly.

```python
from comp.scenario_contracts import (
    RuntimeCase,
    RuntimeProjection,
    write_artifact_envelopes,
    write_runtime_case,
)

runtime_case = RuntimeCase(
    case_id="fixture-case",
    receipts=(receipt,),
    projections=(
        RuntimeProjection(
            public_row_id="public-row-1",
            projection_id="public-row",
            draft_id="draft-1",
            output_fields=("site", "amount"),
            row={"site": "plant-a", "amount": 100},
        ),
    ),
)

write_runtime_case(runtime_case, "prepared/runtime_case.json")
write_artifact_envelopes(artifact_envelopes, "prepared/artifact_envelopes.jsonl")
```

## Running The Bundle

```bash
comp scenario validate scenario.json
comp scenario run scenario.json --report reports/latest.json
```

The resulting report is operational evidence for the scenario run. The report is
not authority; receipts and replay remain the authority path.
