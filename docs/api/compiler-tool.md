# Compiler Tool API Stability

This document classifies the `comp.compiler_tool` package surface by stability.
It is an API reference, not an architecture authority contract.

The important rule is:

```text
README quickstart examples show the stable primary API.
comp.compiler_tool.__all__ is an import-convenience surface.
comp.compiler_tool.__all__ is not the stability contract.
```

`comp.compiler_tool` may export advanced or experimental symbols to keep tests,
examples, and migration code readable. Exported does not mean permanently stable.

## Stable public API

These names are the preferred import surface for package users and README
quickstarts.

```python
from comp.compiler_tool import InterpretationHypothesis, ClaimCandidate, EvidenceRef
from comp.compiler_tool import CompilerTool, ValidationReport
from comp.compiler_tool import resolver_tasks_from_report
from comp.compiler_tool import prepare_commit, build_public_output_receipt
from comp.compiler_tool import compile_report_to_facts
```

### Quickstart input models

These models are stable as quickstart input models. They are stable for
constructing candidate and provenance input to `CompilerTool`. They do not carry
public-output authority.

```text
InterpretationHypothesis
ClaimCandidate
EvidenceRef
```

### Compiler entrypoint

```text
CompilerTool
ValidationReport
```

### Review / resolver handoff

```text
resolver_tasks_from_report
```

### Commit preparation

```text
prepare_commit
build_public_output_receipt
compile_report_to_facts
```

### Quickstart companion gate from top-level `comp`

README quickstarts may pair `comp.compiler_tool` with the top-level public-output
gate:

```python
from comp import PublicOutputBlocked, PublicOutputReceipt, PublicOutputSpec
from comp import build_public_output
```

Those names are owned by the judgment/public-output gate, not by
`comp.compiler_tool`. They appear in the quickstart because the first user path
is only complete when it reaches receipt-gated projection. See
`api/public-output-gate.md` for the top-level gate API.

Stable compiler-tool names:

```text
InterpretationHypothesis
ClaimCandidate
EvidenceRef
CompilerTool
ValidationReport
resolver_tasks_from_report
prepare_commit
build_public_output_receipt
compile_report_to_facts
```

Use these names when writing public examples unless the example is explicitly
teaching an advanced compiler-tool layer.

## Advanced public API

These names are useful for tests, adapters, resolver integrations, and review
tools. They are public enough to import intentionally, but they should not appear
in README quickstarts as the default user path.

```text
SemanticJudgment
ReferenceOption
CanonicalReference
CalculationTrace
CalculatedClaim
ReviewPackage
ReviewDecision
ReferenceCatalog
ReferenceResolver
```

Advanced APIs preserve the authority boundary:

```text
ReferenceOption != CanonicalReference
CalculatedClaim != public output
ReviewPackage != public authority
ReviewDecision != public authority
PublicOutputReceipt == projection gate
```

## Behavior declaration surfaces

These names let domain packs, profiles, fixtures, and reference resources
declare behavior. They are not authority overrides.

```text
DomainPack
CompilerProfile
RuleFamily
SemanticRubric
JudgePolicy
ReferenceCatalog
ReferenceCatalogSnapshot
ReferenceRecord
CalculationFormula
RetrievalQueryPolicy
RetrievalQueryRule
```

DomainPack is a declaration library.
CompilerProfile is the active behavior lock.
Neither is authority.

Behavior declaration surfaces may describe allowed fields, allowed units, active
rules, rubrics, references, formulas, and retrieval policies. The compiler still
owns protocol validation, authority promotion, and receipt-gated projection.

They must not:

```text
mint PublicOutputReceipt
bypass ReferenceOption -> CanonicalReference selection
treat rule output as public authority
authorize projection without receipt
disable core invariants
```

## Experimental / internal-ish API

These names are currently exported for implementation convenience, tests, or
migration support. They should not be treated as stable public API without a PR
that promotes them in this document.

Profile and rule declaration helpers:

```text
profile_declaration_fingerprint
domain_pack_declaration_fingerprint
rule_family_declaration_fingerprint
semantic_rubric_declaration_fingerprint
active_retrieval_query_policies
```

Retrieval and resolver policy helpers:

```text
reference_query_for_requirement_from_policy
reference_query_for_requirement_from_profile_policy
reference_query_for_requirement_from_policies
reference_query_for_requirement_from_resolver_tasks
reference_query_from_resolver_task
```

Reference selection and report mutation helpers:

```text
select_reference_binding
apply_reference_selection
```

Calculation and report retry helpers:

```text
retry_blocked_calculation
apply_calculation_result
```

Adapter and status mutation helpers:

```text
add_compile_report_facts
add_commit_preparation_facts
with_recomputed_status
recompute_report_status
```

Experimental names may still be tested directly. The constraint is that they
must not become accidental README quickstart API.

## Compatibility aliases

Prefer canonical friendly names in new examples. Compatibility aliases may
remain importable for a migration window, but a compatibility alias is not the
preferred quickstart name.

Examples:

```text
ValidationReport is preferred over old report names.
PublicOutputReceipt is preferred over old receipt names.
build_public_output_receipt is preferred over old receipt-builder names.
```

## Promotion rule

To promote an advanced or experimental symbol:

```text
1. Move or add the symbol under the intended stability section here.
2. Update README only if it should become part of the stable quickstart path.
3. Update tests/test_package_smoke.py so the stability class is machine-checked.
4. Preserve receipt-gated authority boundaries.
```

