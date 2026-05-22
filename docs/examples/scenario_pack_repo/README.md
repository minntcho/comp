# comp-scenario-packs Skeleton

This is a copyable downstream repository shape for scenario packs that consume
`comp` through the public scenario bridge.

The downstream repo owns raw data, adapters, larger domain fixtures, benchmarks,
and CI reports. `comp` owns the trust runtime and the receipt/replay contract.

## Minimal Layout

```text
comp-scenario-packs/
  pyproject.toml
  README.md
  .github/workflows/scenario-contracts.yml
  packs/
    public_projection_smoke/
      scenario.json
      prepared/runtime_case.json
      prepared/artifact_envelopes.jsonl
      reports/latest.json
```

Create the first smoke pack with:

```bash
comp scenario init packs/public_projection_smoke
comp scenario run packs/public_projection_smoke/scenario.json
```

After that, replace the prepared files with pack-produced trust inputs. Keep the
same public contract:

```text
raw domain/product input
  -> downstream pre-trust adapter
  -> prepared RuntimeCase + ArtifactEnvelope bundle
  -> comp scenario run
```

## Rules

Do not import `tests.*`.
Do not import private `comp` modules.
Do not make raw CSV, email, OCR, LLM, or product workflow execution part of
`comp`.

Allowed public surfaces:

```text
comp.scenario_contracts
comp.runtime
comp.persistence public interfaces
comp.compiler_tool public interfaces
comp.judgment public interfaces
```

## CI Command

The minimal CI check should install the downstream pack and run the public
scenario CLI:

```bash
python -m pip install -e .
comp scenario run packs/public_projection_smoke/scenario.json
```

The report is compatibility evidence for the pack. It is not authority;
receipts and replay remain the authority path.
