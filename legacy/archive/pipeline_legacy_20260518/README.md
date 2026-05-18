# Legacy Pipeline Archive

This directory is the archive target for the pre-cutover ESGDL pass pipeline.

The archived pipeline is reference material. It is not the active authority
boundary for the rebuild branch.

---

## Why This Exists

The legacy pipeline is useful history, but its core concepts must not become
the new kernel:

```text
CompileArtifacts as shared mutable state
row.status as commit truth
GovernancePass mutating rows into public state
merge_log and event_log as receipt substitutes
pass-owned semantic authority
legacy/package parity as success
```

The active rebuild direction is:

```text
CompilerTool
-> CompileReport / ProofObligations
-> Judgment Facts
-> Governance Decision
-> Receipt
-> Projection
```

---

## Archive Candidates

Pipeline modules:

```text
artifacts.py
lex_pass.py
parse_pass.py
scope_resolution_pass.py
inference_pass.py
semantic_pass.py
repair_pass.py
emit_pass.py
governance_pass.py
calculation_pass.py
pipeline_runner.py
compiled_pipeline_runner.py
compiled_spec.py
binder.py
runtime_env.py
rule_eval.py
rule_ir.py
source_eval.py
source_ir.py
lex_eval.py
lex_ir.py
esg_builtins.py
rule_builtins.py
esgdl.lark
```

Compatibility surfaces:

```text
comp.compat
comp.pipeline
legacy runner exports
```

Legacy-oriented tests:

```text
row.status / merge_log / event_log contract tests
golden tests for legacy row-pipeline behavior
compiled runner parity tests
repair-stage smoke tests
lex/source stage semantics tied to the legacy pass pipeline
```

---

## Test Collection Policy

Archived tests must not be collected by active pytest runs.

When tests are copied here, store them as reference material using one of these
forms:

```text
reference_tests/*.py.txt
reference_tests/*.md
explicit pytest collection exclusions
```

Do not let archived tests define the active pass/fail status of the rebuild.

---

## Non-Goals For This Declaration

This declaration does not:

```text
move legacy files
delete active files
change pyproject packaging
change runtime behavior
implement CompilerTool
create public projection
```

