# Kill List

이 문서는 장기 구조에서 authoritative state로 살아남으면 안 되는 개념을 고정합니다.

목표는 기존 코드를 즉시 삭제하는 것이 아닙니다. 목표는 어떤 개념이 더 이상 진실을 소유하면 안 되는지 먼저 명시하는 것입니다.

---

## 1. Must not survive as authoritative state

다음 항목은 compatibility나 legacy transport로 잠시 남을 수 있지만, 장기 source of truth가 되면 안 됩니다.

```text
row.status as commit truth
GovernancePass mutating rows directly
CommitReceipt stored primarily in row metadata
CompileArtifacts as kernel state
pass-owned semantic authority
indefinite compatibility wrappers
legacy/package parity as architecture success criteria
```

---

## 2. Row status as commit truth

`CanonicalRowArtifact.status`는 projection 상태를 표시할 수는 있지만, commit의 진실이 되면 안 됩니다.

Commit 여부는 governance decision과 receipt가 소유해야 합니다.

```text
Bad:
  row.status == "merged" means this row is public truth

Target:
  decision.action == "commit"
  receipt proves why the projection is allowed
```

---

## 3. Governance mutating rows directly

Governance는 판정자입니다. Governance가 row를 직접 바꾸면 decision과 apply가 섞입니다.

```text
Bad:
  GovernancePass evaluates policy and mutates row.status

Target:
  governance.evaluate(...) -> CommitDecision
  app.apply(decision, projection_state)
```

---

## 4. Receipt as row metadata

Receipt는 부속 metadata가 아니라 first-class output이어야 합니다.

```text
Bad:
  row.metadata["commit_receipt"] = ...

Target:
  ReceiptLedger[receipt_id] = receipt
  row.receipt_ref = receipt_id
```

Row는 receipt를 참조할 수 있지만, receipt의 primary home이 되면 안 됩니다.

---

## 5. CompileArtifacts as kernel state

`CompileArtifacts`는 현재 staged pipeline을 이어가기 위한 legacy transport입니다.

장기 kernel은 `CompileArtifacts`를 import하거나 내부 state로 삼으면 안 됩니다.

```text
Bad:
  kernel function accepts CompileArtifacts

Target:
  kernel accepts evidence / judgment / decision inputs
  legacy adapter translates CompileArtifacts into kernel inputs
```

---

## 6. Pass-owned semantic authority

Pipeline pass는 orchestration boundary일 수 있지만, semantic authority를 영구 소유하면 안 됩니다.

```text
RepairPass owns final selection semantics      -> no
GovernancePass owns commit truth by mutation  -> no
EmitPass owns public truth                    -> no
```

Target:

```text
selection -> judgment
commit decision -> governance
public representation -> projection
pipeline pass -> orchestration/apply
```

---

## 7. Indefinite compatibility wrappers

Compatibility wrapper는 임시 bridge입니다.

Wrapper가 남아야 한다면 다음이 필요합니다.

```text
why it exists
what it preserves
when it can die
what must replace it
```

기한이나 제거 조건이 없는 wrapper는 architecture가 됩니다. 이 상태를 피해야 합니다.

---

## 8. Legacy/package parity as architecture success

Package import와 legacy import가 같은 객체인지 확인하는 parity test는 relocation safety에는 유용합니다.

하지만 그것은 architecture success criterion이 아닙니다.

장기 구조에서는 다음 테스트가 더 중요합니다.

```text
core does not import legacy artifacts
governance does not mutate rows
public rows require receipt references
row is projection, not commit authority
compat adapters do not gain semantic authority
```

---

## 9. Review rule

새 PR은 다음 질문에 답해야 합니다.

```text
이 PR은 kill list 항목을 줄이는가?
아니면 kill list 항목을 더 공식화하는가?
```

후자라면 migration이 아니라 architecture regression입니다.
