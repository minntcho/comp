# LLM Worker Orchestration

Status: north-star
Owner: agent-layer
Last checked against code: 2026-05-20
Can block PRs: limited

This document captures the current working hypothesis for LLM orchestration in
the `comp` rebuild. It builds on the existing authority boundary:

```text
LLM proposes.
Compiler validates.
Receipt authorizes public projection.
```

The central claim is:

```text
LLM tool calling is not an output-format trick.
It is an orchestration step for submitting typed, non-authoritative artifacts.
```

This is not a lockfile for future implementation. It should guide experiments,
make current assumptions visible, and give future work something concrete to
revise. If implementation evidence or domain scenarios contradict this note,
the note should change.

---

## 1. Role Of The LLM

The LLM should be a background worker, not a judge.

It may:

```text
read source units
notice missing or ambiguous slots
propose reading candidates
propose reference queries
draft semantic judgments
ask human-review questions
explain blockers and traces
abstain when context is insufficient
```

It must not:

```text
create ReferenceBinding directly
create DerivedClaim directly
create GovernanceDecision
create CommitReceipt
project public rows
mark missing evidence as satisfied by assumption
turn embedding similarity into truth
activate domain rules or profiles by itself
```

The LLM can be smart and active, but it should only submit artifacts. The
compiler decides whether those artifacts discharge obligations.

---

## 2. Structured Input As Implicit Sentences

Structured rows, forms, and table fragments should not be treated as isolated
cells. A submission unit often carries an implicit sentence grammar.

Example:

```text
Site          Activity      Amount    Unit    Period
Seoul office  Electricity   1200      kWh     2024
```

This is not natural language, but it can be read as:

```text
Seoul office used 1200 kWh of electricity in 2024.
```

The LLM should therefore read submission units as sentence-like objects:

```text
actor / site
activity
quantity
unit
period
geography
method or context
evidence spans
```

This reading is still only a candidate. It must preserve whether each slot was
observed, inferred, missing, or ambiguous.

---

## 3. Candidate Reading Artifacts

An initial LLM reading should submit a candidate artifact, not a checked claim.

Shape:

```text
ReadingCandidate
  source_unit_id
  sentence_type
  slots
    name
    value
    status: observed | inferred | missing | ambiguous
    evidence_refs
  ambiguity_group_id
  rationale
```

Important rules:

```text
observed requires source evidence
inferred is not public evidence
missing is a useful result, not a failure
ambiguous should preserve multiple plausible readings
```

The compiler can convert missing, inferred, or ambiguous slots into
ProofObligations. It can convert supported observed slots into checked claims
only after deterministic validation.

---

## 4. Tool Calls As Artifact Submission

In this system, an LLM tool call should not mutate compiler state directly.

It should submit a typed artifact candidate:

```text
submit_reading_candidate(...)
submit_ambiguity_set(...)
mark_slot_missing(...)
submit_reference_query(...)
submit_semantic_judgment(...)
ask_human_question(...)
abstain_with_reason(...)
```

The tool call means:

```text
I propose this artifact for compiler validation.
```

It does not mean:

```text
This obligation is resolved.
```

The compiler or selector must still validate the submitted artifact against
the active profile, source evidence, obligations, reference catalog, and core
invariants.

---

## 5. LLM Work Orders

The orchestrator should not pass a raw CompileReport directly to the LLM.
Instead, it should create a small work order.

```text
LLMWorkOrder
  work_order_id
  target_id
  target_kind
  task_kind
  context_bundle
  allowed_tools
  forbidden_outputs
  expected_artifacts
  budget
```

The work order narrows the LLM call.

Example:

```text
target: row-17
task_kind: read_submission_unit
allowed_tools:
  submit_reading_candidate
  submit_ambiguity_set
  mark_slot_missing
  abstain_with_reason
forbidden_outputs:
  create_reference_binding
  create_commit_receipt
  project_public_row
```

The same model can then act as different workers depending on the work order:

```text
reading worker
reference-query worker
semantic-judgment worker
human-question worker
critic worker
```

The model is not given all tools all the time.

---

## 6. Obligation-Indexed Tool Menus

The allowed tool menu should follow the current obligation or source-reading
stage.

Initial structured-input reading:

```text
submit_reading_candidate
submit_ambiguity_set
mark_slot_missing
abstain_with_reason
```

Reference gap:

```text
submit_reference_query
explain_reference_need
abstain_with_reason
```

Semantic judgment:

```text
submit_semantic_judgment
flag_conflict
abstain_with_reason
```

Human-needed state:

```text
ask_human_question
explain_blocker
compress_related_questions
```

This keeps tool calling tied to compiler obligations instead of turning the LLM
into an unconstrained agent.

---

## 7. Profile-Generated Tool Schemas

Long term, the tool schema should be generated from domain profiles or sentence
grammar definitions.

Example profile fragment:

```text
activity_quantity
  required slots:
    site
    activity
    amount
    unit
    period
  optional slots:
    geography
    method
```

The orchestrator could expose a generic tool:

```text
submit_reading_candidate(sentence_type, slots, evidence_refs)
```

or a profile-specific tool:

```text
submit_activity_quantity_reading(site, activity, amount, unit, period, ...)
```

The first implementation should not need dynamic tool generation. The design
should leave room for it so prompts, validation, tests, and domain profiles can
eventually share the same source of truth.

---

## 8. Abstention Is A First-Class Artifact

The LLM must be allowed to say it cannot resolve something from available
context.

Abstention tools are mandatory:

```text
abstain_with_reason
cannot_resolve_from_available_context
need_human_input
```

Good result:

```text
unit may be kWh, but no row, header, caption, or nearby context supports it.
```

Bad result:

```text
electricity usually uses kWh, so unit = kWh observed.
```

The system should prefer honest incompleteness over unsupported completion.

---

## 9. Embedding As Routing Context

Embedding similarity must not become a truth score.

Bad:

```text
similarity > 0.90
-> obligation resolved
```

Allowed:

```text
embedding recalls nearby examples, rejected patterns, profiles, and prior work orders
-> orchestrator creates a narrower work order
-> LLM submits an artifact
-> compiler validates it
```

Embedding is a routing signal, not authority.

It can help find:

```text
near accepted examples
near rejected examples
competing semantic clusters
similar obligations
prior successful work orders
prior failed work orders
human-question precedents
relevant sentence-type profiles
relevant tool grammar templates
```

Rejected neighbors are especially valuable because they show the LLM what not
to fake.

---

## 10. Semantic Neighborhood Reports

Embedding-backed retrieval should produce a non-authoritative neighborhood
artifact.

Shape:

```text
SemanticNeighborhoodReport
  report_id
  target_id
  target_kind
  embedding_model_id
  index_snapshot_id
  query_artifact_digest
  accepted_neighbors
  rejected_neighbors
  profile_neighbors
  tool_grammar_neighbors
  competing_clusters
  neighborhood_state
  routing_hints
  authority = non_authoritative_routing_signal
```

Important:

```text
routing_hints are not decisions
neighbors are not evidence
distances are not confidence scores
```

The orchestrator may use this report to choose a work-order kind or context
bundle. The report itself must not discharge obligations.

Useful neighborhood states:

```text
familiar_case
near_miss
conflicting_neighborhood
novel_case
rejected_pattern_match
batchable_gap
human_compressible
```

These states describe what the next constrained action should consider. They do
not say the claim is true.

---

## 11. Neighborhood-Informed Work Orders

When a neighborhood report influences LLM orchestration, that influence should
be recorded.

```text
LLMWorkOrder
  created_from:
    obligation_id
    neighborhood_report_id
  task_kind
  context_bundle
  allowed_tools
  forbidden_outputs
```

Example:

```text
task_kind: find_or_abstain_unit_evidence
context_bundle:
  target row
  table header
  near accepted unit-evidence example
  near rejected unit-inference example
allowed_tools:
  submit_slot_evidence_candidate
  mark_slot_missing
  mark_slot_ambiguous
  abstain_with_reason
```

The work order is informed by embedding, but still created by orchestrator
policy.

---

## 12. Batching And Human Question Compression

Embedding can also group similar unresolved obligations.

Instead of asking:

```text
What is the unit for row 1?
What is the unit for row 2?
What is the unit for row 3?
```

The orchestrator may ask:

```text
Do all numeric values in Table 3, Electricity consumption, use kWh?
```

This is useful when many obligations share a probable root cause:

```text
same table header
same section title
same missing period context
same method ambiguity
same rejected inference pattern
```

Batching is an orchestration optimization. It does not lower compiler
validation requirements for any individual claim.

---

## 13. Authority Boundaries

These invariants should be preserved:

```text
LLM tool calls submit artifacts only.
Submitted artifacts do not mutate compiler authority directly.
Embedding reports are routing context only.
Embedding similarity never resolves an obligation.
Top-1 retrieval never creates ReferenceBinding.
Accepted neighbors do not prove the current case.
Rejected neighbors do not reject the current case by themselves.
LLMWorkOrder can restrict tools, but cannot weaken compiler invariants.
Only compiler validation can discharge obligations.
Only GovernanceDecision plus CommitReceipt can authorize public projection.
```

---

## 14. Suggested Implementation Slices

First slice:

```text
LLMWorkOrder model
allowed tool menu model
ReadingCandidate artifact model
abstain artifact model
deterministic fake LLM worker for tests
```

Current implemented subset:

```text
LLMWorkOrder model
semantic-judgment work-order creation from ResolverTask
AbstentionArtifact
DeterministicLLMWorker fixture
apply_llm_worker_results for submitted SemanticJudgment artifacts
```

This subset is intentionally semantic-only. It gives the agent layer a typed
artifact-submission loop without adding a real LLM provider, a reading candidate
model, or projection authority.

Acceptance criteria:

```text
LLM work orders expose only stage-appropriate tools.
Reading candidates preserve observed / inferred / missing / ambiguous slots.
Abstention is accepted as a valid worker result.
No submitted artifact can authorize projection.
```

Second slice:

```text
SemanticNeighborhoodReport model
deterministic neighborhood resolver stub
near accepted / rejected examples
neighborhood-informed work-order creation
```

Acceptance criteria:

```text
embedding similarity alone never resolves an obligation
rejected neighbors can trigger critic-oriented work orders
competing clusters can trigger ambiguity-oriented work orders
neighborhood reports remain non-authoritative routing signals
```

Third slice:

```text
obligation clustering
batch work orders
minimal human-question generation
```

Acceptance criteria:

```text
similar obligations can be grouped without merging claim authority
cluster-level questions cite the obligations they cover
individual obligations still require compiler validation before commit
```

---

## 15. Open Questions

```text
Should LLMWorkOrder live in comp.compiler_tool or a separate agent namespace?
Should ReadingCandidate become a core artifact or remain extractor-side?
How much of a sentence-type profile should be serializable?
Should tool menus be plain data, Python callables, JSON Schema, or all three?
When should a neighborhood report be recorded as a judgment Fact?
What is the minimum trace needed to replay a neighborhood-informed work order?
How should privacy-sensitive source spans be represented in embedding indexes?
How should human answers become resolver artifacts without becoming receipts?
```
