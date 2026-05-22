# Memory-Assisted Compiler Loop

Status: active-contract
Owner: agent-layer
Last checked against code: 2026-05-22
Can block PRs: yes

This document fixes the integration boundary between `comp` and a
Hermes-style memory/skill agent layer such as `minchoagnt`.

The goal is not to make memory authoritative. The goal is to let memory and
skills improve future hypotheses while `comp` remains the case-level proof
system.

```text
Memory can suggest.
Skills can guide.
LLM can propose.
Compiler must validate.
Judgment must record.
Receipt must authorize.
```

---

## 1. Layer Split

`comp` and `minchoagnt` solve different problems.

```text
comp.judgment
  = case-level evidence, hazards, obligations, and receipts

minchoagnt memory
  = cross-case durable experience that helps future hypothesis generation

minchoagnt skills
  = reusable procedures for resolving recurring obligations
```

They must not compete for authority.

```text
Judgment answers:
  Why is this result valid for this case?

Memory and skills answer:
  What did prior cases teach the agent to try next time?
```

The shortest form is:

```text
minchoagnt learns how to satisfy comp.
comp proves whether the satisfaction is valid.
```

---

## 2. Authority Boundary

The active `comp` architecture remains:

```text
InterpretationHypothesis
-> CompilerTool
-> ValidationReport / ValidationRequirements
-> Judgment Facts
-> Governance Decision
-> Receipt
-> Projection
```

The memory-assisted loop adds an outer adaptive layer:

```text
Memory / Skills / Session Trace
-> LLM or deterministic proposer
-> InterpretationHypothesis
-> comp.CompilerTool
-> ValidationReport
-> comp.judgment Facts
-> Receipt-gated Projection
```

`minchoagnt` may improve the next `InterpretationHypothesis`. It may record
compiler-report-derived facts through the public adapter path, but it must not
mint freestanding `Fact`, `PublicOutputReceipt`, or public projection authority.

Allowed:

```text
Read memory before proposing a hypothesis.
Select skills for an obligation family.
Revise a hypothesis after a ValidationReport.
Reflect on ValidationReport traces.
Propose memory or skill updates with provenance.
```

Forbidden:

```text
Treat memory as evidence.
Treat a skill as a compiler rule.
Turn an accepted ValidationReport into a public row.
Create a PublicOutputReceipt from an LLM response.
Use session logs as receipt authority.
Use row.status, merge_log, or legacy pipeline state as truth.
```

---

## 3. Integration Direction

`comp` should not import `minchoagnt`.

`comp` stays deterministic and import-light:

```text
No Ollama client.
No long-term agent memory.
No SKILL.md procedural store.
No session database.
No self-authored tool policy.
```

The orchestration layer may import `comp`:

```python
from comp.compiler_tool import CompilerTool, InterpretationHypothesis
from comp.compiler_tool import compile_report_to_facts, resolver_tasks_from_report
from comp.judgment import Fact, JudgmentState, SubjectRef
```

This keeps the dependency direction honest:

```text
agent layer depends on compiler authority
compiler authority does not depend on agent memory
```

### 3.1 Agent Core Boundary Contract

The import boundary is part of the contract, not just a packaging preference.

`comp` must not import `minchoagnt`.

`minchoagnt` may import `comp.compiler_tool` report, resolver-task, and fact-adapter contracts.

`minchoagnt` may import judgment value types needed to hold report-derived facts,
such as `Fact`, `JudgmentState`, and `SubjectRef`.

`minchoagnt` must not import `PublicOutputReceipt`, receipt builders, replay engines, or projection gates.

`CompCompilerAdapter` records report-derived facts and leaves receipt issuance to `comp` governance and receipt paths.

Agent output is proposal and resolution material, not projection authority.

This is machine-checked by `tests/test_authority_import_boundaries.py`.

---

## 4. ValidationReport As Learning Signal

`ValidationReport` is not a receipt. It is a structured diagnostic and obligation
surface.

Examples:

```text
FailedClaim(field="unit", reason="missing_source_witness")
ValidationRequirement(kind="find_source_witness", field="unit")
UnknownClaim(field="reporting_year", reason="context_required")
UncheckedArea(field="factor_period_compatibility", reason="missing_rule_coverage")
```

For `comp`, these block or constrain authority.

For the agent layer, these become learning signals:

```text
Which evidence source did we miss?
Which search procedure worked?
Which semantic area lacked rule coverage?
Which hypothesis habit caused repeated blocked reports?
```

The loop is:

```text
ValidationReport / Judgment trace
-> reflection
-> memory and skill candidates
-> future hypothesis improvement
-> CompilerTool validation again
```

---

## 5. Memory Rules

Memory is a hypothesis-generation aid, not truth.

Good memory:

```text
For this report family, unit evidence is often in table column headers.
Month-only periods in annual ESG reports often require cover-page year context.
Factor-period compatibility failures usually require factor table metadata.
```

Bad memory:

```text
Unit is kWh for this supplier, so source witness is unnecessary.
Reporting year can be inferred without source context.
Factor compatibility can be skipped for this report family.
```

Memory entries should be read as search hints, not as claims.

Any memory write derived from a `comp` run should include provenance in its
review evidence:

```text
compile_report_id or run_id
subject_id
obligation or hazard id
source fragment or witness id when available
resolution summary
```

If provenance is missing, the memory candidate should remain review material,
not active memory.

---

## 6. Skill Rules

Skills are obligation-resolution procedures. They are not compiler rules.

Good skill:

```text
Resolve find_source_witness(unit):
1. Inspect the same fragment.
2. Inspect nearby headers.
3. Inspect table column units.
4. If no source witness exists, remove the unit claim or keep a missing_unit hazard.
5. Re-run CompilerTool.
```

Bad skill:

```text
If unit is missing, assume kWh and continue.
```

Skills may guide where the agent looks. They must not weaken compiler
requirements.

Agent-authored skills should have a lifecycle:

```text
candidate
-> reviewed
-> active
-> deprecated
```

Only reviewed active skills should be loaded by default. Candidate skills may be
shown in a workbench, but they should not silently change production behavior.

---

## 7. Unknown And Unchecked Handling

The cutover terminology remains binding.

```text
UnknownClaim
  = a known validation family needs more evidence or context

UncheckedArea
  = no active rule family exists for that semantic area
```

Agent memory must not collapse either state into pass.

Allowed responses:

```text
UnknownClaim(reporting_year)
  -> search for context, ask review question, or keep unknown

UncheckedArea(factor_period_compatibility)
  -> propose rule-acquisition path, request review, or keep unchecked
```

Forbidden responses:

```text
UnknownClaim -> public claim
UncheckedArea -> pass
```

`UncheckedArea` is especially useful as a rule-learning trigger, but any rule
proposal must go through a rule compiler or equivalent governance path before it
changes future compiler behavior.

---

## 8. Workbench Shape

A useful future workbench should make the boundary visible:

```text
Hypothesis
-> CompilerTool
-> ValidationReport
-> Obligations
-> Memory / Skill Reflection
-> Revised Hypothesis
-> Judgment Facts
-> Receipt
```

The workbench may show:

```text
memory used
skills selected
initial hypothesis
compile report
obligations
revisions
new memory candidates
new skill candidates
judgment facts
receipt preconditions
projection block or success
```

It must not hide the authority transition. A public row is only explainable after
receipt authority exists.

---

## 9. Suggested Implementation Sequence

### Phase A: Docs

Add this document and keep it independent from concurrent README or architecture
policy PRs.

### Phase B: Agent-Side Comp Adapter

Add an adapter outside `comp` core, preferably in the agent/orchestration layer.

Initial shape:

```text
InterpretationHypothesis
-> CompilerTool.compile_interpretation(...)
-> ValidationReport
```

No real LLM call is required for this slice.

### Phase C: ValidationReport Reflection

Translate selected `ValidationReport` patterns into memory or skill candidates.

Example:

```text
ValidationRequirement(find_source_witness, unit)
-> candidate skill: resolve missing unit witness
```

### Phase D: Deterministic Revision Loop

Use fixtures first:

```text
hypothesis_v1
-> ValidationReport(blocked)
-> deterministic revised hypothesis fixture
-> ValidationReport(review_required or accepted)
```

### Phase E: Interpretation Engine

Add an LLM-backed proposer only after deterministic fixtures define the contract.

This should produce interpretation hypotheses or interpretation plans, not
receipts.

### Phase F: Workbench

Extend a review workbench to visualize the compiler loop and memory/skill
reflection.

---

## 10. Non-Goals

This document does not authorize:

```text
Importing minchoagnt into comp core.
Adding an LLM provider to comp.
Promoting memory entries into judgment facts.
Promoting skills into compiler rules.
Replacing PublicOutputReceipt with SessionDB or ReviewPlan.
Restoring legacy row.status or merge_log authority.
Creating public projection without PublicOutputReceipt.
```

---

## 11. Summary

The combined architecture should be:

```text
comp
  = case-level proof system

minchoagnt-style layer
  = cross-case learning system
```

The healthy loop is:

```text
Memory recalls prior obligations.
Skills guide how to resolve them.
LLM proposes the next hypothesis.
CompilerTool checks it.
Judgment records the trace.
Receipt authorizes publication.
```

If this boundary holds, the agent becomes more capable without making the public
truth boundary softer.
