# Authority Map

This is the active architecture policy for the rebuild branch.

The goal is to decide ownership before moving files.

---

## Authoritative state

Long-term authoritative state:

```text
Evidence-backed Judgment
Governance Decision
Receipt Ledger
```

Public rows, CSV files, JSON output, and report-facing views are derived projections.

---

## Legacy transport

The following concepts may remain for compatibility, but they are not the long-term authority boundary:

```text
CompileArtifacts
frame runtime metadata
row status fields
pipeline pass metadata
legacy event and merge logs
```

---

## Ownership rules

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
Is the result hold, commit, or reject?
What receipt explains the decision?
```

Projection answers:

```text
How is a committed decision represented externally?
```

Runner/app code assembles these layers and may handle legacy adapters.

---

## Review rule

Before relocating a module, answer:

```text
What authority does this module own today?
Should that authority remain here long term?
If not, which layer should own it instead?
```

If those answers are unclear, architecture correction comes before relocation.
