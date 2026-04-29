# Views and Ledger

이 문서는 `comp`에서 **무엇이 본체 상태이고 무엇이 view/projection인가**를 설명합니다.

중요:
이 문서는 단순 UI 문서가 아닙니다.
여기서의 view는 화면을 뜻하는 것이 아니라,
판정 상태를 바깥에서 읽기 좋은 형태로 **다시 materialize한 표현**을 뜻합니다.

---

## 왜 이 문서가 필요한가

`comp`를 row 중심으로만 보면,
다음이 쉽게 흐려집니다.

- row가 source of truth인가
- draft와 public row는 어떻게 다른가
- emit은 state mutation인가 export인가
- selection/commit의 이유는 어디에 남는가
- review/explanation은 본체 상태인가 파생 view인가

장기 구조에서는 이 질문을 분명히 갈라야 합니다.

핵심 기준은 이겁니다.

> **본체는 judgment state와 receipt/log 쪽에 더 가깝고,**
> **draft/review/public/explanation은 그 상태를 보는 view에 가깝다.**

---

## authoritative state

장기적으로 authoritative state에 가까운 것은 다음 셋입니다.

### 1. JudgmentState / FactStore

가장 중심이 되는 것은 판정 사실들의 상태입니다.

여기에는 대체로 다음이 포함됩니다.

- candidate 관련 사실
- evidence 관련 사실
- hazard 관련 사실
- provenance 관련 사실

즉 public row보다 먼저,
**무엇이 판정되었는가**가 본체입니다.

### 2. ReceiptLog

selection과 commit의 이유는 append-only 기록으로 남아야 합니다.

대표적으로는:

- `SelectionReceipt`
- `CommitReceipt`

이 로그가 있어야
“왜 이 후보가 선택되었는가”,
“왜 지금 commit이 hold 되었는가”를 다시 설명할 수 있습니다.

### 3. PublicLedger

public row는 아무 row나 임시로 찍어 두는 캐시가 아니라,
commit barrier를 통과한 결과를 바깥으로 append하는 공개 기록에 가깝습니다.

즉 public 쪽의 핵심은 “현재 row 스냅샷”보다
**정당한 공개 상태의 누적 기록** 입니다.

---

## derived view

다음 것들은 장기적으로 authoritative state 그 자체라기보다,
그 상태를 다시 읽기 좋게 표현한 derived view에 가깝습니다.

### DraftView

아직 public commit 되지 않은 상태를 본 view입니다.

예:
- 현재 active candidate
- 열린 hazard
- unresolved bundle
- provenance 상태

### ReviewView

자동 단일 결론보다 검토가 필요한 상태를 강조한 view입니다.

예:
- frontier가 여러 개인 bundle
- stale selection
- commit blocked draft

### PublicExport

외부 시스템이나 다운스트림 계산이 읽기 쉬운 public projection입니다.

예:
- canonical row export
- merge 대상 row snapshot

### ExplanationView

판정 사실과 receipt를 사람이 읽기 좋게 정리한 설명 view입니다.

예:
- 왜 winner가 바뀌었는가
- 왜 merge가 hold 되었는가
- 어떤 evidence와 hazard가 현재 상태를 만들었는가

중요:
설명 문자열이 본체가 아니라,
설명은 fact/receipt를 읽기 쉽게 다시 만든 **파생 결과** 입니다.

---

## emit은 mutation보다 materialization에 가깝다

장기 구조에서 emit을 별도 source-of-truth pass로 두면,
다음이 쉽게 섞입니다.

- 현재 판단 상태
- 외부에 보여 주기 위한 field projection
- merge 가능한지 여부

그래서 장기적으로 emit은
state 본체를 만드는 단계라기보다,
**판정 결과를 특정 schema/view로 materialize하는 단계**로 보는 것이 더 자연스럽습니다.

이 관점이 있으면 다음 구분이 쉬워집니다.

- row가 보인다고 바로 merge 상태는 아니다
- draft view가 존재한다고 public ledger에 append된 것은 아니다
- explanation이 있다고 source of truth가 바뀌는 것은 아니다

---

## append-only와 재계산의 경계

장기적으로는 모든 것을 append-only로 둘 필요는 없습니다.

구분은 이렇게 잡는 편이 좋습니다.

### append-only로 남길 것

- judgment fact의 누적 상태
- selection/commit receipt
- public ledger 기록

### 재계산 가능한 것

- draft view
- review view
- explanation view
- public export snapshot

즉 “다 저장한다”가 아니라,
**무엇을 authoritative하게 남기고 무엇을 projection으로 다시 만들지**를 분리해야 합니다.

---

## 현재 레포의 실제 연결점

현재 레포는 아직 이 모델을 완전히 구현하지는 않았습니다.

하지만 다음 연결점은 이미 있습니다.

### `comp.views.public`

public row materialization helper를 제공하며,
projection 관점을 코드로 옮기기 시작한 부분입니다.

### `EmitPass`

아직 `artifacts.rows`를 채우지만,
장기적으로는 view/materialization 계층으로 더 내려갈 수 있는 위치에 있습니다.

### `SelectionReceipt` / `CommitReceipt`

selection과 commit의 이유를 별도 기록으로 남기기 시작한 vocabulary입니다.

### `GovernancePass`

merge/hold 결정과 commit receipt append를 통해,
barrier와 public append 개념을 일부 반영합니다.

즉 지금 레포는 row를 아직 물리적으로 materialize하지만,
동시에 row를 projection으로 다시 보려는 vocabulary도 함께 도입한 상태입니다.

---

## 목표 상태

장기적으로는 대략 다음 그림이 자연스럽습니다.

- core: JudgmentState / FactStore
- append-only logs: ReceiptLog / PublicLedger
- derived views: DraftView / ReviewView / PublicExport / ExplanationView

이 구조가 되면,
row와 explanation과 review 화면이 서로 독립 저장소가 아니라
**같은 판정 세계를 보는 다른 창문**이 됩니다.

---

## 요약

`comp`에서 중요한 것은 row를 많이 만드는 것이 아닙니다.

더 중요한 것은:

- 무엇이 authoritative state인가
- 무엇이 append-only 기록인가
- 무엇이 projection/view인가

를 분리하는 것입니다.

장기적으로 `comp`는
**judgment state + receipt/public ledger를 본체로 두고,**
**draft/review/public/explanation을 그 위의 view로 두는 구조**를 지향합니다.
