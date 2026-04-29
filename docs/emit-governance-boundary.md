# Emit / Governance Boundary

이 문서는 현재 staged pipeline 안에서 `EmitPass`와 `GovernancePass`의 책임 경계를 분리해서 설명한다.

목표는 두 가지다.

1. 현재 코드가 실제로 무엇을 하는지 정확히 적는다.
2. 장기 judgment-first 구조에서 이 경계가 어떤 의미로 이동해야 하는지 분리해서 적는다.

중요:
이 문서는 코드 relocation 문서가 아니다.
`EmitPass`와 `GovernancePass`의 의미 경계를 설명하는 architecture 문서다.

---

## 한 줄 요약

```text
EmitPass
  committed frame을 canonical row 형태로 materialize하는 projection boundary

GovernancePass
  materialized row를 policy / commit barrier로 평가해 merge / hold / skip을 결정하는 barrier boundary
```

즉 emit은 “row를 공개해도 되는지 최종 판정하는 단계”가 아니고,
governance는 “row field를 만드는 단계”가 아니다.

---

## 현재 pipeline에서의 위치

현재 기본 실행 순서는 다음과 같다.

```text
RepairPass
→ EmitPass
→ GovernancePass
→ CalculationPass
```

이 구간에서 상태는 대략 이렇게 흐른다.

```text
PartialFrameArtifact(status="committed")
→ CanonicalRowArtifact(status="committed")
→ GovernanceDecisionArtifact(action="merge" | "hold" | "skip")
→ row.status = "merged" when allowed
→ CalculationArtifact for merged rows
```

현재 구현에서 row는 아직 `artifacts.rows`에 물리적으로 저장된다.
그러나 장기 구조의 설명 언어에서는 이 row를 authoritative state 자체가 아니라,
판정 상태를 외부 schema로 읽기 좋게 만든 projection으로 본다.

---

## EmitPass의 책임

현재 `EmitPass`의 핵심 책임은 다음이다.

```text
committed frame + active claims + runtime env
→ canonical row materialization
```

조금 더 풀면 다음과 같다.

- committed frame을 대상으로 한다.
- frame slot의 active claim을 읽는다.
- `comp.views.public`의 projection helper를 통해 canonical row를 만든다.
- 만들어진 row를 `artifacts.rows`에 둔다.
- row field를 채우지만 merge 여부를 최종 결정하지 않는다.

따라서 `EmitPass`는 다음을 하지 않아야 한다.

- governance policy 평가
- merge / hold / skip 최종 결정
- public ledger append 의미 부여
- commit receipt 생성
- calculation 수행

현재 코드에서는 `EmitPass`가 row를 물리적으로 만들기 때문에 이름상 “emit”이 강하게 보일 수 있다.
하지만 architecture 관점에서는 emit을 **projection materialization boundary**로 읽는 것이 더 정확하다.

---

## GovernancePass의 책임

현재 `GovernancePass`의 핵심 책임은 다음이다.

```text
canonical row + compiled governance policy + commit barrier adapter
→ merge / hold / skip decision
```

조금 더 풀면 다음과 같다.

- row status를 확인한다.
- frame type에 맞는 governance policy를 찾는다.
- emit condition / forbid merge / merge condition을 평가한다.
- commit barrier adapter를 통해 stale / hazard / provenance snapshot을 본다.
- `GovernanceDecisionArtifact`를 `merge_log`에 남긴다.
- event를 `event_log`에 남긴다.
- merge가 허용되면 row status를 `merged`로 바꾼다.
- commit receipt에 가까운 기록을 `commit_log`와 row metadata에 남긴다.

따라서 `GovernancePass`는 다음을 하지 않아야 한다.

- raw fragment에서 token/claim 생성
- frame slot candidate selection
- canonical row field projection 자체
- emission factor 계산
- judgment core 전체 실행으로 대체되는 것처럼 행동

즉 governance는 **barrier / decision / receipt-adjacent boundary**다.

---

## 현재 구현 사실과 target semantics의 차이

이 경계에서 가장 중요한 점은 현재 구현과 장기 목표를 섞지 않는 것이다.

### 현재 구현 사실

현재 구현은 staged pipeline이다.

- `RepairPass`가 frame status를 `committed`, `review_required`, `rejected`, `resolving` 등으로 정리한다.
- `EmitPass`는 기본적으로 committed frame만 row로 materialize한다.
- materialized row는 `artifacts.rows`에 저장된다.
- `GovernancePass`가 그 row에 대해 merge / hold / skip을 결정한다.
- `commit_log`, `merge_log`, `event_log`는 이미 있지만 장기 public ledger 전체 모델은 아직 아니다.

### 장기 target semantics

장기적으로는 다음 구분이 더 강해져야 한다.

- authoritative state: judgment facts / hazards / provenance / receipts
- projection view: draft / review / public export / explanation
- public ledger: commit barrier를 통과한 공개 기록

이 관점에서 canonical row는 source of truth가 아니라 public/export schema에 가까운 projection이다.
Governance는 그 projection이 public state로 승격될 수 있는지를 판단하는 barrier다.

---

## 두 가지 hold를 구분하기

현재 pipeline에서는 “hold”를 두 층으로 나누어 읽어야 한다.

### 1. emit 전 hold

frame이 committed 상태가 아니면 기본 `EmitPass`는 row를 만들지 않을 수 있다.

예:

```text
frame.status = "review_required"
→ EmitPass does not materialize a row by default
```

이 경우는 governance가 row를 hold한 것이 아니다.
아직 governance 대상 row가 생기지 않은 상태다.

### 2. governance hold

frame은 committed 되었고 row도 materialize되었지만,
governance policy나 commit barrier가 merge를 허용하지 않을 수 있다.

예:

```text
row.status = "committed"
→ GovernancePass action = "hold"
→ row.status remains "committed"
```

이 경우는 governance boundary에서 merge가 막힌 것이다.

이 구분은 중요하다.
둘을 섞으면 “row가 없음”, “draft는 있음”, “public merge가 안 됨”, “review가 필요함”이 모두 같은 상태처럼 보인다.

---

## 로그와 receipt의 역할 구분

현재 implementation에서 관련 기록은 다음처럼 나뉜다.

```text
artifacts.rows
  materialized canonical row snapshots

artifacts.merge_log
  governance decision records

artifacts.event_log
  stage-visible event records

artifacts.commit_log
  commit receipt-adjacent records

row.metadata["commit_receipt"]
  row-local copy of commit receipt-like data
```

장기적으로는 이 구분을 더 명확히 해야 한다.

- row snapshot은 projection이다.
- merge log는 decision trace다.
- event log는 execution/event history다.
- commit receipt는 barrier 통과 이유를 설명하는 append-only 근거다.
- public ledger는 commit된 공개 상태의 누적 기록이다.

현재 코드는 이 전체 모델을 완성한 상태가 아니라,
그 vocabulary와 bridge를 일부 도입한 상태다.

---

## CalculationPass와의 경계

`CalculationPass`는 governance 이후에 온다.

현재 기본 계산은 merged row만 대상으로 한다.
따라서 calculation은 다음으로 읽는 것이 자연스럽다.

```text
public/merged row
→ post-commit derivation
→ calculation artifact
```

즉 calculation은 emit도 아니고 governance도 아니다.

- emit은 row schema projection을 만든다.
- governance는 row의 public 승격 여부를 판단한다.
- calculation은 승격된 row를 읽어 후속 값을 계산한다.

---

## 이 경계를 지키는 이유

이 경계를 지키면 다음 문제가 줄어든다.

1. `EmitPass`가 policy decision을 몰래 담는 문제
2. `GovernancePass`가 row projection logic을 몰래 담는 문제
3. row snapshot을 authoritative state로 오해하는 문제
4. commit receipt와 human explanation을 섞는 문제
5. calculation이 merge 전 draft를 읽는 문제

즉 이 경계는 단순 코드 정리가 아니라,
장기 judgment-first 구조로 가기 위한 설명상의 안전선이다.

---

## PR에서 지켜야 할 기준

emit / governance 주변 PR은 다음 기준을 따른다.

### 허용

- projection helper 이름 정리
- decision / receipt / log 용어 정리
- docs에서 current fact와 target semantics 분리
- no-behavior-change helper extraction
- row materialization과 governance decision 사이의 테스트 강화

### 금지

- import convergence와 architecture refactor를 한 PR에 섞기
- runner relocation과 emit/governance refactor를 섞기
- `EmitPass`에 merge/hold decision 추가하기
- `GovernancePass`에 canonical row field materialization 추가하기
- calculation behavior를 같이 바꾸기
- current bridge를 완성된 public ledger 모델처럼 문서화하기

---

## 현재 기준으로 보는 다음 방향

이 문서는 경계 문서다.
바로 큰 refactor를 요구하지 않는다.

다음 단계는 작은 단위로 나누는 편이 좋다.

1. current pipeline 문서에서 emit/governance 구분을 이 문서로 링크한다.
2. tests에서 committed frame → row materialization → governance decision 흐름을 더 명확히 잠근다.
3. 필요하면 governance receipt construction을 작은 helper boundary로 빼되 behavior를 바꾸지 않는다.
4. 장기적으로 judgment core가 selection/commit 일부를 본류에서 직접 담당하게 한다.

---

## 같이 읽을 문서

- `current-pipeline.md`
- `views-ledger.md`
- `worked-example.md`
- `judgment-core.md`
- `migration-checklist.md`
