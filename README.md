# comp

`comp` is a rebuild branch for an evidence-preserving compiler.

This branch starts from the PR #14 judgment-core point. It does not continue the later package migration as the active direction.

The goal is to decide authority first, then move code.

---

## Core claim

`comp` is not primarily a row generator.

It is a compiler that should explain whether a public output is justified.

The intended flow is:

```text
raw fragment
→ evidence / claim
→ judgment
→ governance decision
→ receipt
→ public projection
```

The table is not the source of truth. The judgment trail and receipt are the source of truth.

---

## Active policy

Read these first:

```text
docs/architecture/authority-map.md
docs/architecture/kill-list.md
```

These documents define what may own authority in the rebuild branch.

---

## Authoritative concepts

Long-term authority belongs to:

```text
Evidence-backed Judgment
Governance Decision
Receipt Ledger
```

Derived outputs include:

```text
Public row
CSV / JSON output
DataFrame view
Report-facing projection
```

Legacy transport includes:

```text
CompileArtifacts
frame runtime metadata
row status fields
pipeline pass metadata
legacy event and merge logs
```

Legacy transport may remain for compatibility, but it should not become the long-term source of truth.

---

## What this branch is not

This branch is not a continuation of relocation-first migration.

It does not treat these as architecture success criteria:

```text
moving files into package paths
making legacy and package imports point to the same object
preserving behavior before deciding whether the behavior should survive
keeping wrappers without an explicit reason
```

Those can be useful migration tools, but they are not the target architecture.

---

## Rebuild rule

Before moving a module, answer:

```text
What authority does this module own today?
Should that authority stay here long term?
If not, which layer should own it?
```

If the answer is unclear, architecture correction comes before relocation.

---

## Layer ownership

Evidence answers:

```text
Where did this value come from?
What source, claim, provenance, or conflict is attached?
```

Judgment answers:

```text
Which candidate is selected?
Why was it selected?
What derivation or justification exists?
```

Governance answers:

```text
Can this judgment be made public?
Is the decision hold, commit, or reject?
What receipt explains the decision?
```

Projection answers:

```text
How is a committed decision represented externally?
```

Runner/app code assembles these layers and may handle legacy adapters.

---

## Preserved migration state

The later migration state is preserved separately at:

```text
legacy/current-migration-state-20260429
```

Historical migration documents are reference material. They are not active policy for this rebuild branch.

See:

```text
docs/archive/2026-migration/README.md
```

---

## Current status

This branch is an architecture reset point.

Current intent:

```text
1. keep the PR #14 judgment-core baseline
2. define authority ownership
3. prevent legacy transport from becoming the new source of truth
4. build a small vertical slice before continuing relocation
```

Next useful slice:

```text
fragment
→ claim
→ judgment
→ governance decision
→ receipt
→ projected row
```

That slice should work before broad migration continues.
