# 2026-05-28 Document Refresh Queue

Authority: none

This queue cannot block PRs. This queue must not be cited as current guidance.

This queue records suspected refresh candidates after the document lifecycle
ratchet. A queue entry is a maintenance signal, not proof that the document is
wrong. Close an entry by refreshing the document, confirming no drift, or
demoting/archiving the document if it no longer carries current guidance.

## Handling Rules

```text
Queue item -> anchor check -> one of:
  refresh
  confirm no drift
  demote/archive
```

Do not use this queue as an authority contract. If a queue item needs enforceable
review behavior, move that behavior into a governed architecture document and its
tests.

## Refresh Candidates

| doc | issue | required anchor check | target action |
|---|---|---|---|
| `docs/architecture/north-stars/production-trust-spine-database.md` | north-star should stay direction-only as MySQL backend behavior grows | `comp/persistence/mysql.py`, `tests/test_mysql_persistence_spine.py`, and `tests/test_mysql_operating_contract.py` | confirm no drift or refresh |
| `docs/architecture/north-stars/llm-worker-orchestration.md` | north-star should not read like current agent authority | `comp/compiler_tool/resolver_tasks.py` and agent-facing public boundary tests | confirm no drift or demote/archive |

