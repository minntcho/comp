# Profile / Schema Selection Resolution Tiers

This note captures the current working shape for profile and schema selection in the internal execution pipeline.

It does not freeze API names, class names, module layout, implementation order, or a final algorithm. It records the intended execution distinction between deterministic contract resolution, semantic candidate retrieval, and judgment-assisted selection.

## Core Idea

Profile and schema selection should not treat every unresolved attribute the same way.

The selection path should separate three levels of work:

```text
Tier 1: declared contract resolution
Tier 2: embedding candidate retrieval
Tier 3: LLM judgment aid
```

The tiers are ordered by authority and cost, not by intelligence.

```text
Resolve with declared contract first.
Use embeddings only when the declared contract cannot close the case.
Use LLM judgment only when retrieved candidates and context still need interpretation.
```

A later tier should not overwrite an earlier tier that already closed the requirement under the selected contract.

## Shared Observation Bundle

Before the tiered selection path runs, the system may build a reusable observation bundle from raw or extracted material.

Example input:

```text
fuel_used = 1200
plant = "A"
month = "2026-01"
source text = "Plant A used 1200 L diesel in 2026-01."
```

A reusable observation bundle may include:

```text
source field name
raw value
value shape
unit hints
neighboring fields
source span or witness snippet
normalized tokens
embedding vector or lookup key
previous failed requirements
previous held decisions
```

This bundle can be created early, reused by later tiers, or saved as loop material when selection is deferred.

The bundle is not authority. It is evidence and context used by selection mechanisms.

## Tier 1: Declared Contract Resolution

Tier 1 handles cases that can be closed by already selected contract material.

Examples:

```text
canonical fields:
  amount
  site
  period
  activity_type
  unit

alias mappings:
  fuel_volume_liters -> amount
  plant -> site
  month -> period
```

If incoming material matches the declared contract, selection can be deterministic:

```text
fuel_volume_liters -> amount
plant -> site
month -> period
```

Tier 1 can select material when:

```text
the field is already canonical
or a declared alias/mapping exists
and the selected profile allows that field
and no conflict blocks the mapping
```

Tier 1 output may become selected validation contract material.

Invalid satisfiers:

```text
A source field looking familiar.
A model recommendation.
A scenario fixture using the same field name.
An embedding score.
```

## Tier 2: Embedding Candidate Retrieval

Tier 2 handles unresolved attributes that were not closed by declared contract material.

Example:

```text
fuel_used = 1200
```

If no declared mapping exists, embedding retrieval may produce candidates:

```text
candidate: amount
candidate: fuel_volume
candidate: fuel_cost
```

Embedding retrieval is useful for narrowing the search space, but it should not automatically activate a field.

Default Tier 2 output:

```text
candidate mappings
proposal material
hold-for-decision material
```

A profile may allow limited auto-selection from embeddings, but only under explicit policy constraints such as:

```text
high enough score
large enough margin over alternatives
low-risk field
no conflicting candidate
selected profile permits embedding-based auto-selection
```

Even then, the basis should be recorded as embedding-policy selection, not declared-contract selection.

Invalid satisfiers:

```text
Top embedding score alone.
Stable deterministic embedding output alone.
Similarity to a known field without selection policy.
```

## Tier 3: LLM Judgment Aid

Tier 3 handles unresolved selection cases where contract rules and embedding candidates are not enough.

The LLM should receive structured context, not just raw text.

Possible input:

```text
source attribute:
  fuel_used = 1200

source context:
  "Plant A used 1200 L diesel in 2026-01."

embedding candidates:
  amount
  fuel_volume
  fuel_cost

selected profile fields:
  amount
  unit
  activity_type
  site
  period
```

LLM output should be treated as judgment aid or recommendation material.

Example:

```text
recommendation:
  fuel_used -> amount
reason:
  value is a usage quantity paired with L and diesel context
requires_selection:
  true
```

The LLM does not validate claims, does not activate schema by itself, does not close requirements by itself, and does not authorize public projection.

Default Tier 3 output:

```text
recommended mapping
reasoned candidate ranking
hold-for-decision material
need-more-evidence material
```

Invalid satisfiers:

```text
LLM confidence alone.
Natural-language explanation alone.
A plausible semantic reading without selected-policy acceptance.
```

## Deferral and Loop Reuse

Some attributes should not be forced into a selection on the first pass.

Example:

```text
fuel_used -> ambiguous
candidates: amount, fuel_volume, fuel_cost
missing clue: unit or activity context
```

The correct output may be:

```text
hold
record candidate set
record missing clues
wait for more evidence or a later revision loop
```

If later evidence arrives:

```text
unit = L
activity_type = diesel
```

then the same observation bundle and candidate set can be reused in a later selection loop.

The important rule is:

```text
Do not close ambiguous selection merely to keep the pipeline moving.
```

## Selection Output Shape

Profile and schema selection should produce more than a selected contract.

A useful output shape includes:

```text
selected contract material
  fields, units, mappings, rules, and policies active for validation

deterministic selections
  material selected by declared contract or explicit profile rule

candidate selections
  embedding or LLM-suggested candidates that are not active

held material
  unresolved attributes that require decision or more evidence

rejected material
  attributes excluded from validation with reasons

selection basis
  declared_contract
  alias_table
  profile_policy
  embedding_policy
  llm_recommendation
  user_or_review_decision
```

Only selected contract material can feed claim validation.

## Main Boundary

The tiered process should preserve this chain:

```text
Declared contract can select.
Embedding can retrieve candidates.
LLM can assist judgment.
Selection policy decides what becomes active.
Compiler validates only the selected contract input.
Receipt and replay remain public-output authority.
```

The key distinction is:

```text
Computationally deterministic output is not the same as contractually selected material.
```

Embedding output may be stable. LLM output may be repeatable under controlled settings. Neither fact makes the output active validation contract material.

Contractual selection requires declared rules, selected policy, profile decision, user/review approval, or another recognized selection mechanism.
