# Judgment Core

이 문서는 `comp`의 장기 구조로서 **judgment-first architecture**를 설명한다.

중요:
이 문서는 완전히 미래의 이야기만 적는 문서가 아니다.
현재 레포에 이미 들어온 judgment vocabulary와,
그 vocabulary가 기존 pipeline에 어디까지 연결되었는지도 함께 적는다.

또한 이 문서는 다음을 전부 대신하지 않는다.

- 공통 판정 언어 전체: `judgment-language.md`
- 코어 의미론 전체: `core-semantics.md`
- 목표 실행 모델 전체: `execution-model.md`

즉 이 문서의 중심은
**현재 레포에 judgment core가 어디까지 들어와 있는가** 이다.

---

## 왜 judgment core가 필요한가

현재 staged pipeline은 동작한다.
하지만 다음 문제가 남는다.

- 왜 이 candidate가 선택되었는가
- 왜 이 row는 아직 public state가 아닌가
- 왜 emit은 가능하지만 merge는 hold인가
- data와 spec을 같은 판정 언어로 설명할 수 있는가

이 문제를 풀려면 row보다 먼저
**판정 가능한 사실들의 세계**를 세워야 한다.

---

## 핵심 생각

`comp`의 장기 구조는 다음과 같이 요약할 수 있다.

1. raw 입력은 seed fact로 올라간다.
2. spec/DSL은 monotone transfer rule로 컴파일된다.
3. core는 fixpoint engine 위에서 동작한다.
4. candidate selection은 frontier 계산으로 처리한다.
5. public row는 commit barrier를 통과한 projection만 허용한다.
6. selection과 commit은 receipt를 남긴다.

---

## 현재 들어와 있는 judgment 객체

현재 패키지에는 이미 다음 개념이 존재한다.

### core
- `SubjectRef`
- `Fact`
- `JudgmentState`
- `FactTag`
- `SubjectKind`

### program
- `TransferRule`
- `BundleSpec`
- `CommitSpec`
- `ProjectionSpec`
- `CompiledJudgmentProgram`

### execution
- `FixpointEngine`

### selection
- `CandidateSummary`
- `dominates`
- `frontier`
- `winner_or_none`
- `needs_review`

### commit
- `DraftSnapshot`
- `committable`
- `project_public_row`

### receipts
- `SelectionReceipt`
- `CommitReceipt`

즉 judgment core는 이미 “문서상의 목표”가 아니라
**패키지 안에 실제 코드로 존재하는 상태**다.

---

## judgment vocabulary의 의미

### Fact
모든 중요한 상태를 먼저 fact로 떨어뜨린다.

예:
- candidate proposal
- evidence 추가
- hazard open
- hazard discharge
- provenance edge

### JudgmentState
append-only fact 집합과 subject version을 가진다.

### TransferRule
어떤 fact 변화가 들어왔을 때 새 fact를 더 생성하는 rule이다.

### FixpointEngine
더 이상 새 fact가 생기지 않을 때까지 monotone rule을 반복 적용한다.

### CandidateSummary / frontier
전체 후보를 다 저장한 뒤 하나를 즉시 지우는 구조가 아니라,
요약된 candidate summary들 사이의 dominance 관계를 보고
frontier를 계산한다.

### DraftSnapshot / committable
 draft가 public state로 승격 가능한지 판단하는 barrier 표현이다.

### ProjectionSpec / project_public_row
public row를 source of truth로 보는 대신,
판정 결과로부터 materialize되는 projection으로 본다.

---

## 현재 pipeline과의 실제 연결점

judgment core는 아직 주 실행 모델을 대체하지 않았다.
그러나 이미 몇 군데에 실제로 연결되어 있다.

### 1. RepairPass ↔ selection receipt
`RepairPass`는 slot repair 이후 selection receipt를 저장한다.
이 receipt는 judgment 쪽 frontier/winner vocabulary와 연결되는 첫 bridge다.

### 2. EmitPass ↔ views / projection
`EmitPass`는 row 조립을 직접 다 하지 않고,
`comp.views`의 public projection helper에 위임하기 시작했다.

### 3. GovernancePass ↔ commit barrier
`GovernancePass`는 row snapshot을 judgment-style `DraftSnapshot`으로 보고,
`committable`을 통해 hold/merge 여부를 일부 설명한다.

### 4. compat.adapters ↔ 기존 artifact 구조
현재 row, slot, claim, lineage는 아직 legacy artifact 구조가 중심이다.
`comp.compat.adapters`는 이 구조를 judgment vocabulary로 번역하는 bridge 역할을 한다.

---

## 현재 한계

현재 judgment core는 아직 다음 단계까지는 가지 않았다.

1. 메인 runner가 judgment program을 직접 실행하지 않는다.
2. `CompiledJudgmentProgram`이 본류 DSL lowering 결과는 아니다.
3. frontier가 repair loop 전체를 장악하지 않는다.
4. public ledger가 artifact row를 완전히 대체하지 않았다.

즉 지금 judgment core는
**실행 본류를 대체한 코어라기보다, 장기 구조를 미리 세운 의미층 + adapter 층**이다.

---

## 같이 읽을 문서

- 공통 판정 언어: `judgment-language.md`
- 코어 의미론: `core-semantics.md`
- 목표 실행 모델: `execution-model.md`
- view / ledger 구분: `views-ledger.md`
- 앞으로의 정리 순서: `migration-plan.md`

---

## 요약

현재 judgment core는 아직 본류를 장악한 상태는 아니다.
그러나 이미 다음 역할을 시작했다.

- selection vocabulary 제공
- commit vocabulary 제공
- projection vocabulary 제공
- legacy artifact를 새 판단 언어로 번역하는 bridge 제공

즉 지금 레포에서 judgment core는
**실험 메모가 아니라, 본류로 올라오기 시작한 의미 축**이다.
