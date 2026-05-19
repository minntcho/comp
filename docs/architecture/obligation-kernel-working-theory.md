# Obligation Kernel Working Theory

Status: working theory, not final architecture.

This document captures the current direction for the rebuild branch after the
receipt-gated projection slice. It is intentionally not an ADR. The goal is to
make the current design pressure visible, keep the unsafe paths out of the code,
and give the next PR a concrete target.

The working thesis is:

```text
comp should not become an ESG-specific compiler.

comp core should be an obligation / judgment / receipt kernel.
ESG, GHG Protocol, Scope 2, factor compatibility, and similar meanings belong
in domain packs.
```

---

## 1. Problem

ESG data extraction is not fully deterministic.

Many important checks are semantic judgments:

```text
Does this evidence span support this claim?
Does this table header apply to this cell?
Does this wording imply market-based Scope 2?
Does this factor table apply to this reporting period?
Is this number an amount, an invoice id, or a total?
```

A deterministic validator cannot honestly answer all of those questions by
itself. But an unconstrained LLM answer also cannot become publication
authority.

The system needs to expose those semantic gaps instead of hiding them.

---

## 2. Current Thesis

The compiler-like part of the system should be understood as an obligation
compiler:

```text
Candidate
-> required proof / judgment obligations
-> resolved artifacts
-> validation of those artifacts
-> governance
-> receipt
-> projection
```

The core does not decide domain truth. The core manages the protocol by which a
candidate becomes publishable.

In short:

```text
Extractor proposes.
Validator opens obligations.
Resolver resolves obligations.
Validator verifies resolution artifacts.
Governance commits.
Publisher projects.
```

---

## 3. Core / Domain Split

### Core Owns

Core owns generic protocol objects and invariants:

```text
EvidenceSpan
Claim envelope
CompileReport
ProofObligation
SemanticJudgment
Judgment facts
GovernanceDecision
CommitReceipt
Receipt-gated projection
```

Core should know that a claim exists. It should not know what an ESG claim
means.

The claim envelope can carry:

```text
claim_id
claim_type
payload
evidence_refs
origin
```

The domain pack owns the payload schema and semantic meaning.

### Domain Pack Owns

Domain packs own domain meaning:

```text
claim schemas
field schemas
rule families
semantic rubrics
judge policy candidates
extraction hints
projection specs
taxonomy mappings
```

ESG-specific concepts must live in a domain pack, not in core:

```text
Scope 2
market-based
location-based
supplier-specific emission factor
GHG Protocol
materiality
factor period compatibility
electricity unit compatibility
```

### Compiler Profile Owns

A compiler profile locks a concrete runtime configuration:

```text
profile_id
core invariant version
domain pack ids / versions / hashes
active rule ids
active rubric ids
selected judge policy id
selected projection policy id
```

Installed domain packs are not automatically active. Available rules are not
automatically active. New versions are not automatically used.

The profile is the lockfile for behavior.

### Resolver Owns

Resolvers are non-authoritative workers:

```text
LLM
human reviewer
parser
searcher
table interpreter
memory-assisted agent
```

Resolvers satisfy obligations by submitting artifacts such as:

```text
SemanticJudgment
EvidenceLink
ContextAttachment
RuleProposal
ReviewDecision
```

Resolvers do not bypass validation and do not publish.

---

## 4. Obligation Loop

The central loop should be:

```text
Candidate
  |
Deterministic validator / obligation compiler
  |
CompileReport
  - checked claims
  - failed claims
  - unknown claims
  - unchecked areas
  - open obligations
        |
Non-deterministic resolver
  - SemanticJudgment
  - EvidenceLink
  - ContextAttachment
  - RuleProposal
  - ReviewDecision
        |
Deterministic validator again
        |
Judgment facts
        |
Governance decision
        |
CommitReceipt
        |
Projection
```

The validator is not a truth oracle. It is an obligation oracle.

Its job is to expose:

```text
what evidence is missing
what context is missing
what semantic judgment is required
what rule coverage is missing
what conflicts remain unresolved
```

---

## 5. Obligation Types

The current `ProofObligation` concept should grow toward a small family of
obligation types:

```text
EvidenceSearchObligation
  Find or attach source evidence.

ContextObligation
  Attach reporting year, entity, period, boundary, or similar context.

SemanticJudgmentObligation
  Ask a judge to decide whether cited evidence supports/refutes a claim under a rubric.

ConflictResolutionObligation
  Resolve conflicting candidates, evidence links, or judgments.

RuleCoverageObligation
  Mark that the active profile has no rule/rubric for this semantic area.

HumanReviewObligation
  Require a human decision for a blocked or high-risk case.
```

This list is not final. The next PR should start with the minimum useful slice:

```text
SemanticJudgmentObligation
SemanticJudgment
obligation discharge validation
```

---

## 6. Semantic Judgment

A semantic judgment is not a receipt. It is not a public projection authority.
It is an artifact that attempts to satisfy a semantic obligation.

Minimum shape:

```python
@dataclass(frozen=True)
class SemanticJudgment:
    judgment_id: str
    obligation_id: str
    verdict: str
    rubric_id: str
    judge: str
    cited_span_ids: tuple[str, ...]
    rationale: str
    confidence: float | None = None
```

The core should not interpret the domain meaning of `verdict`. The core should
validate protocol sufficiency:

```text
Does obligation_id match an open obligation?
Is the rubric_id the required rubric?
Is the verdict in acceptable_verdicts?
Is the judge allowed by the selected profile policy?
Do cited_span_ids exist?
Is there an active conflicting judgment?
```

Confidence is advisory. It is not authority.

---

## 7. Domain Rules

Domain rules should declare proof requirements. They should not weaken core
invariants.

Example domain rule shape:

```python
class Scope2MethodSupportRule:
    rule_id = "ghg.scope2_method_support.v1"

    def evaluate(self, claim, context):
        if claim.claim_type != "scope2_method":
            return ()

        return (
            ProofObligation(
                kind="semantic_judgment_required",
                claim_id=claim.claim_id,
                opened_by_rule_id=self.rule_id,
                domain_id="ghg_protocol",
                question="Does the cited span support the claimed Scope 2 method?",
                rubric_id="ghg-protocol-scope2-method-v1",
                acceptable_verdicts=("supports", "refutes", "ambiguous"),
                blocking=True,
            ),
        )
```

Core does not need to know what `scope2_method` or `market_based` means. It only
needs to know that an obligation was opened and whether a submitted artifact
satisfies the protocol.

---

## 8. Core Invariants

Domain packs may add requirements. They must not weaken these invariants:

```text
CommitReceipt is required for public projection.
An accepted CompileReport alone is not projection authority.
Open blocking obligations block commit and projection.
Unchecked areas are not pass.
Unknown claims are not public claims.
LLM-only values are not source-backed public claims.
Memory is not evidence.
Skills are not rules.
Conflicting active semantic judgments block commit.
Domain packs cannot mark missing evidence as satisfied by assumption.
```

The core is allowed to reject a domain pack or compiler profile that attempts to
weaken these invariants.

---

## 9. DSL Direction

DSL should not encode final truth. DSL should declare proof workflows.

The useful target for DSL is a domain pack:

```text
DSL source
-> DomainPack
-> RuleFamily / SemanticRubric / JudgePolicy candidate / ProjectionSpec
-> CompilerProfile activation
```

The DSL should make this easy to express:

```text
concept scope2_method:
  type enum["market_based", "location_based"]

  requires semantic_judgment:
    question "Does the cited span support the claimed Scope 2 method?"
    rubric "ghg-protocol-scope2-method-v1"
    acceptable_verdicts supports, refutes, ambiguous
    required_verdict supports
    judge approved_llm_or_human
    blocking true

  publish:
    require no_open_blocking_obligations
    require commit_receipt
```

The DSL compiler compiles domain meaning into obligation protocol. It does not
authorize publication.

---

## 10. Lark And Extractors

Lark, regex extractors, table extractors, and LLM hypothesis generators are
extractor plugins. They are not core dependencies.

Core should not import Lark.

Extractor outputs should enter the system as generic artifacts:

```text
EvidenceSpan
ClaimHypothesis
ParseDerivation
CandidateMapping
```

Extractors must not create checked, selected, committed, or projected states.

---

## 11. Reference-Grounded Calculation

LLM numeric scoring is unsafe.

The system should not ask an LLM to decide:

```text
which emission factor is correct
whether a calculated value is reasonable
whether a disclosure deserves an 87/100 score
whether a vector-search top result is the true concept
```

Numeric evaluation should be reference-grounded:

```text
embedding = candidate retrieval
reference DB = canonical definitions
deterministic selector = reference binding
calculator = derived claim generation
quality score = coverage metadata, not truth authority
```

This is not plain RAG. It is a reference-grounded calculation pipeline.

### Reference Flow

The intended flow is:

```text
Source evidence
-> extractor / LLM / Lark / table parser
-> ClaimHypothesis
-> reference resolver
   - embedding search
   - alias search
   - taxonomy lookup
   - factor candidate retrieval
-> ReferenceCandidateSet
-> deterministic filter
   - unit compatible?
   - period compatible?
   - geography compatible?
   - method compatible?
   - source priority acceptable?
-> ReferenceBinding
-> calculator
   - unit conversion
   - factor application
   - uncertainty metadata
   - calculation trace
-> DerivedClaim
-> validator
-> governance
-> receipt
-> projection
```

Embedding and alias search widen the candidate set. They do not select the
canonical reference by themselves.

### Reference DB

The reference DB is domain authority, not the vector index.

Minimum reference DB families:

```text
TaxonomyConcept
  concept_id
  labels
  aliases
  description
  parent / child relationships
  applicable claim types

MetricDefinition
  metric_id
  required fields
  allowed units
  calculation formula
  required evidence

UnitDefinition
  unit_id
  dimension
  conversion rules

EmissionFactor
  factor_id
  activity / concept id
  geography
  valid period
  method
  unit basis
  source priority
  uncertainty metadata
  source row witness

Formula
  formula_id
  input requirements
  unit conversion requirements
  output unit

Rubric
  rubric_id
  question template
  acceptable verdicts
  allowed judge candidates

ProjectionSpec
  projection_id
  output fields
  required receipt authority
```

Vector indexes may cover:

```text
labels
aliases
descriptions
examples
standard references
factor source descriptions
```

Canonical authority is the reference row id, not vector similarity.

### Reference Candidates

Retrieval output should remain candidate-only:

```python
@dataclass(frozen=True)
class ReferenceCandidate:
    candidate_id: str
    reference_id: str
    reference_type: str
    retrieval_method: str
    retrieval_score: float | None = None
    authority: str = "candidate_only"
```

`retrieval_score` is a ranking hint. It is not a truth score.

The system must not use embedding top-1 as a selected factor, concept, unit, or
metric definition.

### Reference Binding

Reference binding is the point where candidates become usable inputs.

A binding should record the deterministic compatibility checks that selected one
canonical reference and rejected the others:

```text
ReferenceBinding:
  binding_id
  claim_id
  concept_id
  reference_id
  reference_type
  unit_id
  method
  period
  geography
  source_witness_ids
  compatibility_checks
  rejected_candidates
```

Example:

```text
ReferenceBinding:
  claim_id: electricity_amount_123
  concept_id: taxonomy.electricity_consumption
  factor_id: emission_factor.kr_grid_2024
  unit_id: kWh
  method: location_based
  period: 2024-01
  geography: KR
  source_witnesses:
    - span_amount
    - span_unit
    - span_period
    - factor_table_row
  rejected_candidates:
    - supplier_specific_factor_missing_supplier_id
    - residual_mix_factor_method_mismatch
```

If binding cannot be completed deterministically, the validator should open an
obligation instead of guessing:

```text
method unknown
-> SemanticJudgmentObligation or ContextObligation

factor period missing
-> ContextObligation

factor rule family missing
-> RuleCoverageObligation / UncheckedArea

candidate factors conflict
-> ConflictResolutionObligation
```

### Derived Claims

Calculator output is not public output. It is a derived claim.

Example:

```text
1200 kWh * 0.0004 tCO2e/kWh = 0.48 tCO2e
```

Architecture shape:

```text
DerivedClaim:
  claim_type: co2e_emission
  value: 0.48
  unit: tCO2e
  input_claim_ids:
    - activity_amount_claim
  reference_binding_ids:
    - unit_binding
    - emission_factor_binding
  formula_id: electricity_factor_multiplication_v1
  calculation_trace:
    - convert unit if needed
    - multiply by factor
  provenance:
    - amount span
    - unit span
    - factor row
```

The validator should then check:

```text
Are input claims checked?
Are reference bindings accepted?
Is the formula allowed by the active profile?
Is unit conversion valid?
Is the calculation trace complete?
Are there open blocking obligations?
```

Only governance and receipt authority can make a derived claim projectable.

### Evidence Quality

The system may produce an evidence quality report, but it should start as a
vector of coverage states, not a single truth-looking scalar.

Example:

```text
EvidenceQuality:
  source_witness: present
  unit_witness: missing
  period_resolved: present
  geography_resolved: present
  method_resolved: ambiguous
  factor_bound: blocked
  calculation_trace: unavailable
  conflicts: none
  open_obligations:
    - find_source_witness(unit)
    - semantic_judgment_required(scope2_method)
```

If a scalar score is later needed, it must be a deterministic summary of the
coverage vector. It is a quality indicator, not publication authority.

Blocking gates override scores:

```text
score 95 but no CommitReceipt
-> projection blocked

score 95 but unresolved SemanticJudgmentObligation
-> projection blocked

score 95 but factor binding rejected
-> projection blocked
```

### Calculation Invariants

These invariants belong with the core / profile boundary:

```text
Embedding top-1 cannot bind a reference.
LLM cannot assign evidence quality authority.
Retrieval score cannot select a factor.
ReferenceBinding requires deterministic compatibility checks or open obligations.
Calculator output is a DerivedClaim, not public output.
DerivedClaim requires formula_id and calculation trace.
Quality score cannot override open obligations, failed checks, or missing receipt.
CommitReceipt should cite input claim ids, reference binding ids, formula ids, trace ids, and evidence span ids.
```

---

## 12. Scenario Cases

### Missing Source Witness

```text
Candidate:
  unit = kWh
  no cited evidence span

Expected:
  EvidenceSearchObligation is open.
  Public projection is blocked.
```

### Table Header Applies To Unit

```text
Candidate:
  amount = 1200
  unit = kWh
  evidence span = table header "Electricity consumption (kWh)"

Expected:
  SemanticJudgmentObligation asks whether the header applies to the cell.
  Resolver submits SemanticJudgment.
  Validator checks the judgment artifact and discharges the obligation only if sufficient.
```

### Scope 2 Method Support

```text
Candidate:
  scope2_method = market_based
  evidence span = "supplier-specific emission factors"

Expected:
  Domain rule opens a SemanticJudgmentObligation with a GHG Protocol rubric.
  LLM or human may judge only through that obligation.
  A conflicting judgment blocks commit.
```

### Factor Period Compatibility

```text
Candidate:
  activity_period = 2024
  factor_version = 2022 factor table

Expected:
  If active rule exists, it opens required mechanical or semantic obligations.
  If no active rule exists, RuleCoverageObligation or UncheckedArea is reported.
```

### New ESG Concept

```text
Need:
  renewable_energy_certificate

Expected change:
  Add claim schema, rule, rubric, projection spec, and profile activation in a domain pack.
  Do not change core protocol objects unless the new concept reveals a missing generic primitive.
```

### Public Row Trace

```text
Question:
  Why was this value published?

Expected trace:
  CommitReceipt
  -> GovernanceDecision
  -> discharged obligation ids
  -> SemanticJudgment ids
  -> evidence span ids
  -> rule ids
  -> domain pack / profile version
```

### Reference Candidate Retrieval

```text
Source:
  "Purchased electricity 1,200 kWh Seoul office Jan 2024"

Expected:
  Embedding retrieves concept and factor candidates.
  Candidates remain candidate_only.
  Deterministic filter must bind concept, unit, period, geography, method, and factor before calculation.
```

### Factor Binding

```text
Candidate:
  amount = 1200 kWh
  geography = KR
  period = 2024-01
  method is unknown

Expected:
  KR grid location-based factor may be a candidate.
  Supplier-specific or residual mix factors may also be candidates.
  Binding is blocked until method or source priority is resolved.
  Validator opens a ContextObligation or SemanticJudgmentObligation.
```

### Derived Claim

```text
Candidate:
  electricity amount claim is checked
  emission factor binding is accepted
  formula is active in profile

Expected:
  Calculator creates DerivedClaim for emissions.
  DerivedClaim contains formula id, input claim ids, binding ids, and calculation trace.
  DerivedClaim still requires validator / governance / receipt before projection.
```

### Evidence Quality Score

```text
Candidate:
  source witness, period, and geography are present
  unit witness is missing

Expected:
  EvidenceQuality vector reports missing unit witness.
  Any scalar quality score remains advisory.
  Publication remains blocked.
```

---

## 13. Next PR Scope

Recommended next PR:

```text
PR8: Core / Domain Boundary Working Theory
```

Purpose:

```text
Document the working theory before adding new semantic obligation models.
Prevent the next implementation PR from leaking ESG/GHG details into core.
Define the next vertical slice as SemanticJudgmentObligation -> SemanticJudgment -> discharge validation.
```

Deliverables:

```text
docs/architecture/obligation-kernel-working-theory.md
README pointer or architecture index pointer, if the repo wants discoverability.
No runtime behavior change.
No package surface change.
No domain pack implementation yet.
```

Acceptance criteria:

```text
The document explicitly says this is a working theory, not final architecture.
The document separates core, domain pack, compiler profile, resolver, and extractor responsibilities.
The document states core invariants that domain packs cannot weaken.
The document defines SemanticJudgmentObligation as the next vertical slice.
The document states that DSL compiles to domain packs, not publication authority.
The document includes scenario cases for missing witness, table header judgment, Scope 2 method support, factor compatibility, new concept addition, and public row trace.
Existing tests still pass.
```

Non-goals:

```text
No GovernanceDecision implementation.
No new rule engine.
No LLM integration.
No Lark reintroduction into core.
No ESG taxonomy ingestion.
No package rename.
```

The following PR should then be:

```text
PR9: SemanticJudgmentObligation Minimal Slice
```

Candidate scope:

```text
Add generic SemanticJudgmentRequirement / SemanticJudgment models.
Allow a rule to open semantic_judgment_required obligations.
Validate submitted judgments against obligation_id, rubric_id, verdict, judge policy, and cited spans.
Keep ESG specifics in test fixtures or a tiny domain fixture, not core.
```

The reference-grounded calculation work should come after the semantic
obligation slice unless a smaller document-only PR is needed first:

```text
PR10 candidate: ReferenceBinding / DerivedClaim Working Slice
```

Candidate scope:

```text
Add generic ReferenceCandidate / ReferenceBinding / DerivedClaim model envelopes.
Keep reference DB specifics in a tiny domain fixture.
Show that retrieval scores do not bind references.
Show that calculator output remains a derived claim until receipt.
```

---

## 14. Open Questions

These are intentionally unresolved:

```text
Should SemanticJudgment live in compiler_tool or a new core namespace?
Is SemanticJudgment evidence, review artifact, or a separate proof artifact?
Should profiles be plain Python objects, DSL output, TOML/YAML, or all of the above?
How strict should judge policy be for LLM-generated judgments?
How are rubric version migrations handled?
What belongs in GovernanceDecision versus CommitReceipt?
How much of DomainPack should be serializable?
Should DSL compile to DomainPack only, or also to CompilerProfile candidates?
Should ReferenceCandidate / ReferenceBinding / DerivedClaim live in core or compiler_tool?
Should reference DB rows be part of DomainPack, external resources, or both?
How should reference DB versions and vector index versions be pinned in CompilerProfile?
How should evidence quality vectors map to scalar UI indicators without becoming authority?
```

---

## 15. Revision Log

```text
2026-05-19:
  Initial working theory.
  Reframes compiler as an obligation / receipt kernel rather than an ESG-specific compiler.
  Sets the next implementation slice as semantic judgment obligations before broader governance work.
  Adds reference-grounded calculation direction:
    embedding retrieves candidates, deterministic binding selects references, calculator emits derived claims, and quality scores remain advisory.
```
