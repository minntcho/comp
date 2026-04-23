# Judgment Language

이 문서는 `comp`가 장기적으로 공유하려는 **공통 판정 언어**를 설명합니다.

중요:
이 문서는 “현재 코드에 이미 전부 구현된 것”만 적는 문서가 아닙니다.
반대로 완전히 공중에 떠 있는 미래 설계만 적는 문서도 아닙니다.

여기서는 다음을 함께 다룹니다.

- 현재 레포에 이미 들어온 judgment vocabulary
- 앞으로 spec과 data가 같이 공유해야 할 판정 어휘
- 무엇이 judgeable object인가에 대한 기준

---

## 왜 이 문서가 필요한가

`comp`가 하려는 일은 단순히 row를 만드는 것이 아닙니다.

이 레포는 다음 둘을 함께 다뤄야 합니다.

1. **결과물 쪽 대상**
   - claim
   - bundle
   - draft
   - public row

2. **생성 틀 쪽 대상**
   - transfer rule
   - selection policy
   - commit policy
   - projection/schema
   - compiled program

즉 `comp`는 data만 심사하는 시스템이 아니라,
**데이터와 생성 틀을 같이 심사하는 시스템**이어야 합니다.

그러려면 둘이 같은 언어를 공유해야 합니다.
여기서 말하는 “같은 언어”는 같은 문법 파일을 쓴다는 뜻이 아니라,
**같은 판정 어휘와 같은 판정 기록 구조를 공유한다**는 뜻입니다.

---

## judgeable subject

이 문서에서 subject는 “판정의 대상”을 뜻합니다.

### data-side subject

현재와 장기 구조를 함께 보면, data 쪽 subject는 대체로 다음과 같습니다.

- `claim`
  - 개별 후보 주장
- `bundle`
  - 함께 경쟁하거나 함께 묶어야 하는 후보 집합
- `draft`
  - 아직 public state가 되지 않은 중간 상태
- `public_row`
  - commit barrier를 통과한 공개 상태

현재 레포는 frame/slot/row 중심 artifact를 많이 사용하므로,
당분간은 frame/slot 구조가 bundle/draft vocabulary의 bridge 역할을 합니다.

### spec-side subject

장기적으로 spec도 data와 같은 언어로 다뤄야 합니다.

대표적으로는 다음이 subject가 됩니다.

- `transfer_rule`
- `selection_policy`
- `commit_policy`
- `projection`
- `compiled_program`

즉 rule이나 policy도 “그냥 코드 조각”이 아니라,
**판정 가능한 객체**로 취급해야 합니다.

---

## 공통 predicate vocabulary

predicate 이름이 현재 코드와 미래 구조에서 완전히 1:1로 같을 필요는 없습니다.
하지만 다음 판정 어휘는 공통 코어로 유지하는 것이 좋습니다.

### `well_formed`
구조적으로 성립하는가.

- data 쪽: claim/draft/row가 필요한 모양을 갖췄는가
- spec 쪽: rule/policy/projection이 허용된 구조를 따르는가

### `supported`
충분한 근거를 갖는가.

- data 쪽: candidate가 evidence/provenance를 갖는가
- spec 쪽: rule이 정당한 입력/출력 계약 위에 서 있는가

### `conflicted`
서로 배타적인 상태가 동시에 열려 있는가.

### `unsafe`
현재 상태로는 통과시키면 안 되는가.

- data 쪽: hazard가 해소되지 않았는가
- spec 쪽: provenance 없는 shortcut이나 unsafe projection을 허용하는가

### `stale`
현재 선택이나 상태가 최신 판단과 어긋나는가.

### `fresh`
현재 선택이나 상태가 최신 판단을 반영하는가.

### `admissible`
경쟁 후보 중 대표 후보가 될 자격이 있는가.

### `requires_review`
자동으로 단일 결론을 내리기보다 검토로 넘겨야 하는가.

### `committable`
public state로 승격시킬 수 있는가.

중요한 점은,
이 어휘가 data에만 붙는 것이 아니라 spec에도 붙어야 한다는 것입니다.

---

## 판정 사실의 종류

공통 판정 언어는 단순 predicate 이름만으로 끝나지 않습니다.
그 predicate가 왜 성립했는지를 기록하는 fact 구조가 필요합니다.

### evidence fact
어떤 값을 지지하는 근거를 기록합니다.

예:
- source fragment에서 직접 추출됨
- infer rule에 의해 생성됨
- 다른 slot/value를 근거로 도출됨

### hazard fact
commit이나 대표선출을 막는 위험 신호를 기록합니다.

예:
- unresolved conflict
- missing required field
- insufficient provenance
- merge policy block

### provenance fact
현재 상태가 무엇에서 왔는지 기록합니다.

예:
- fragment → claim
- claim → bundle summary
- draft → public row
- rule/policy → decision path

### obligation fact
지금 당장 merge하지 말고 review/repair/approval을 요구하는 상태를 기록합니다.

### receipt
판정의 이유를 남기는 append-only 기록입니다.

- `SelectionReceipt`
- `CommitReceipt`

### explanation record
판정 결과를 사람이 읽을 수 있게 다시 투영한 설명 기록입니다.

중요:
설명은 source of truth가 아닙니다.
설명은 fact와 receipt를 읽기 좋게 다시 표현한 **view** 입니다.

---

## 같은 언어를 data와 spec에 적용하는 방식

### data validation

data 쪽에서는 보통 다음 질문을 합니다.

- 이 candidate는 `supported`한가
- 이 draft는 `well_formed`한가
- 이 winner는 `admissible`한가
- 이 row는 `committable`한가
- 이 상태는 `stale`한가

### spec validation

spec 쪽에서는 보통 다음 질문을 합니다.

- 이 rule은 `well_formed`한가
- 이 selection policy는 `admissible`하지 않은 대표를 허용하는가
- 이 commit policy는 `unsafe`한 row를 막는가
- 이 projection은 provenance 손실을 허용하는가
- 이 compiled program은 `committable`하지 않은 상태를 통과시키는가

즉 validator가 둘인 것이 아니라,
**같은 judgment vocabulary를 서로 다른 subject에 적용하는 것**이 중요합니다.

---

## 현재 레포의 연결점

현재 레포에는 이미 다음 judgment vocabulary가 들어와 있습니다.

- `SubjectRef`
- `Fact`
- `JudgmentState`
- `TransferRule`
- `CommitSpec`
- `ProjectionSpec`
- `SelectionReceipt`
- `CommitReceipt`

또한 다음 bridge도 이미 존재합니다.

- `comp.compat.adapters`
  - legacy artifact를 judgment vocabulary로 번역
- `comp.views.public`
  - projection helper 제공
- `GovernancePass`
  - `DraftSnapshot`과 `committable()`을 사용해 barrier를 평가

즉 이 문서의 내용은 전부 미래 상상만이 아니라,
이미 들어온 코드와 앞으로 강화할 방향을 함께 설명합니다.

---

## 아직 고정되지 않은 것

현재 레포에서 아직 완전히 고정되지 않은 부분도 있습니다.

1. predicate 집합의 최종 이름과 범위
2. obligation lifecycle의 정식 모델
3. explanation record의 표준 스키마
4. spec-side subject 전체를 같은 엔진에서 직접 심사하는 경로

즉 지금 단계에서는 공통 판정 언어의 방향은 잡혔지만,
완전한 canonical schema가 확정된 것은 아닙니다.

---

## 요약

`comp`는 row만 만드는 시스템으로 보면 설명이 부족합니다.

이 레포가 장기적으로 목표로 하는 것은:

- data와 spec을 함께 judgeable object로 보고
- 같은 predicate vocabulary를 공유하고
- evidence / hazard / provenance / receipt를 같은 언어로 남기고
- selection과 commit의 이유를 같은 언어로 설명하는 구조

입니다.

즉 `comp`의 중심 언어는 최종 row schema만이 아니라,
**판정 가능한 세계 전체를 설명하는 judgment language** 입니다.
