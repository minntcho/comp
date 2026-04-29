# Authority Map

이 문서는 `comp` 재정렬의 active architecture policy입니다.

목표는 파일 위치를 정리하는 것이 아니라, 각 개념이 어떤 권한을 갖는지 먼저 고정하는 것입니다. 앞으로의 구조 변경은 이 문서를 기준으로 판단합니다.

---

## 1. Authoritative state

`comp`의 장기 source of truth는 다음 세 가지입니다.

```text
Evidence-backed Judgment
Governance Decision
Receipt Ledger
```

즉 public output은 직접 진실이 아닙니다. public output은 판정과 receipt에서 파생된 projection입니다.

---

## 2. Derived views

다음은 authoritative state가 아니라 derived view입니다.

```text
Public row
CSV / JSON output
DataFrame view
Report-facing projection
```

이들은 외부에 보여주기 위한 표현입니다. 이 표현이 commit 여부나 정당성을 스스로 소유하면 안 됩니다.

---

## 3. Legacy transport

다음은 현재 실행 호환을 위해 남아 있을 수 있지만, 장기 source of truth가 아닙니다.

```text
CompileArtifacts
PartialFrameArtifact runtime metadata
CanonicalRowArtifact.status
pipeline pass metadata
legacy event_log / merge_log coupling
```

이 객체들은 legacy staged pipeline을 유지하기 위한 transport 또는 compatibility layer로만 취급합니다.

---

## 4. Authority rules

### Evidence

Evidence layer는 다음 질문만 소유합니다.

```text
이 값은 어디서 왔는가?
어떤 source / span / claim / provenance가 연결되는가?
어떤 충돌 또는 hazard가 있는가?
```

Evidence layer는 public 여부를 결정하지 않습니다.

### Judgment

Judgment layer는 다음 질문을 소유합니다.

```text
어떤 claim/fact가 선택 가능한가?
왜 이 후보가 선택되었는가?
어떤 derivation 또는 justification이 남는가?
```

Judgment layer는 row를 직접 만들지 않습니다.

### Governance

Governance layer는 다음 질문을 소유합니다.

```text
이 judgment를 public으로 내보내도 되는가?
hold / commit / reject 중 무엇인가?
어떤 reason code와 receipt가 남는가?
```

Governance layer는 row를 직접 mutate하지 않습니다. Governance의 출력은 decision과 receipt입니다.

### Projection

Projection layer는 다음 질문만 소유합니다.

```text
committed decision / receipt를 어떤 public representation으로 보여줄 것인가?
```

Projection layer는 commit 여부를 결정하지 않습니다.

### App / pipeline orchestration

App 또는 runner는 조립과 적용을 담당합니다.

```text
input loading
pipeline sequencing
legacy adapter invocation
output writing
integration behavior
```

App은 모든 조각을 알 수 있지만, core layer가 app orchestration을 알면 안 됩니다.

---

## 5. Import boundary

장기적으로 다음 방향을 지향합니다.

```text
core authority layer -> legacy artifacts import 금지
legacy pipeline -> core authority layer 호출 가능
app/runner -> 모든 layer 조립 가능
```

즉 legacy가 core를 호출하는 것은 허용되지만, core가 legacy artifact에 의존하면 안 됩니다.

---

## 6. Migration rule

앞으로 relocation PR은 다음 조건을 먼저 통과해야 합니다.

```text
1. 이 module이 어떤 authority를 소유하는지 명확한가?
2. 그 authority가 장기 구조에서도 살아남는가?
3. 아니라면 package-owned implementation으로 승격하지 않는가?
4. 기존 behavior를 보존하기 전에, 보존할 가치가 있는 behavior인지 확인했는가?
```

이 조건을 통과하지 못하면 relocation이 아니라 legacy containment 또는 architecture correction이 먼저입니다.
