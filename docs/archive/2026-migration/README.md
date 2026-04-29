# 2026 Migration Archive

이 디렉토리는 이전 package migration / facade / compatibility 문서 흐름을 보존하기 위한 archive입니다.

이 문서들은 삭제하지 않습니다. 다만 active architecture policy로 사용하지 않습니다.

---

## Status

```text
historical reference only
not active implementation guidance
not active architecture policy
```

---

## Why archived?

이전 migration 문서들은 다음 문제를 분석하는 데 가치가 있습니다.

```text
how package relocation proceeded
how bridge state was defined
how wrappers and facades were classified
how no-behavior-change migration protected legacy behavior
how architecture work was deferred into later tracks
```

그러나 rebuild 방향에서는 다음 원칙이 우선합니다.

```text
source of truth before relocation
authority transfer before file movement
legacy containment before package-owned promotion
receipt/decision/projection before row mutation
```

---

## Preserved source

현재 main 상태는 다음 branch에 보존됩니다.

```text
legacy/current-migration-state-20260429
```

이 branch의 docs와 code는 과거 migration state의 증거물입니다.

---

## Active replacements

새 active architecture policy는 다음 문서를 봅니다.

```text
docs/architecture/authority-map.md
docs/architecture/kill-list.md
```

추가 active docs는 이 두 문서의 원칙을 따라 작성해야 합니다.

---

## Rule

이 archive 안의 문서를 근거로 새 implementation 작업을 시작하면 안 됩니다.

필요한 개념은 archive에서 직접 가져오지 말고, active architecture 문서로 재작성한 뒤 사용합니다.
