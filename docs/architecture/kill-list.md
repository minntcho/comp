# Kill List

This document lists concepts that must not become long-term authoritative state.

The goal is not immediate deletion. The goal is to prevent legacy concepts from being promoted as the new authority boundary.

---

## Must not become authoritative

```text
row.status as commit truth
GovernancePass as direct row mutator
CommitReceipt primarily stored in row metadata
CompileArtifacts as kernel state
pass-owned semantic authority
indefinite compatibility wrappers
legacy/package parity as architecture success
```

---

## Target ownership

```text
selection authority -> judgment
commit authority -> governance decision
public representation -> projection
legacy transport -> adapter / app layer
```

---

## Review rule

Every architecture or migration PR should answer:

```text
Does this PR reduce one kill-list item?
Or does it make one kill-list item more official?
```

The first is progress. The second needs an explicit architecture decision.
