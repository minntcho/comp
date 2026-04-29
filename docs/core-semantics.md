# Core Semantics

이 문서는 `comp`의 장기 구조를 **하나의 코어 의미론**으로 설명합니다.

중요:
이 문서는 현재 `pipeline_runner.py`가 실제로 어떻게 돈다는 설명을 대체하지 않습니다.
현재 실행 흐름은 `current-pipeline.md`가 설명합니다.

여기서는 그 위에서,
왜 `comp`를 여러 패스와 여러 저장소의 집합으로만 보지 않고
**하나의 judgment core + 얇은 selection/commit shell** 로 보려 하는지를 설명합니다.

---

## 왜 “하나의 코어”가 필요한가

`comp`의 관심사는 단순 변환이 아닙니다.

이 레포는 다음을 함께 설명해야 합니다.

- 어떤 candidate가 생겼는가
- 무엇이 그것을 지지하는가
- 어떤 hazard가 열려 있는가
- 어떤 provenance가 붙어 있는가
- 왜 이 상태는 아직 public이 아닌가
- 왜 이 representative가 선택되었는가

이걸 각각 다른 subsystem, 다른 저장소, 다른 pass로만 밀어내면
아키텍처가 쉽게 커집니다.

그래서 장기적으로는,
후보/근거/hazard/provenance를 **하나의 판정 우주** 안에서 다루고,
selection과 commit만 얇은 껍질로 남기는 쪽이 자연스럽습니다.

---

## 하나의 judgment state

장기 구조에서 중심 state는 row 테이블이 아니라
**판정 사실들의 상태**입니다.

직관적으로는 다음 좌표를 함께 가진 상태로 볼 수 있습니다.

- candidate 관련 사실
- evidence 관련 사실
- hazard 관련 사실
- provenance 관련 사실

즉 “support store”, “hazard store”, “review store”를 다 독립 본체로 두기보다,
**하나의 judgment state의 다른 좌표**로 보는 쪽이 더 단순합니다.

현재 레포의 `Fact`, `JudgmentState`는 이 방향을 가리키는 core vocabulary입니다.

---

## seed fact와 compiled operator

장기적으로는 data와 spec이 같은 코어에서 만납니다.

### data는 seed fact

raw input은 바로 public row가 되는 것이 아니라,
먼저 seed fact로 올라갑니다.

예:
- token proposal
- parser output claim
- source-linked evidence
- 초기 hazard

### spec은 compiled operator

DSL/spec는 그대로 실행되는 것이 아니라,
judgment state 위에서 작동하는 rule/operator로 내려옵니다.

즉 spec은 대략 다음 역할을 합니다.

- 어떤 fact가 새 fact를 유도하는가
- 어떤 bundle/selection 규칙이 적용되는가
- 어떤 barrier가 commit을 막는가
- 어떤 projection이 public view를 정의하는가

그래서 data와 spec은 각각

- `seed`
- `compiled operator`

로 하나의 코어에서 만나는 구조가 됩니다.

---

## least fixpoint 관점

이 구조를 가장 짧게 말하면,
실행은 “패스를 한 번씩 지나간다”보다
**고정점을 푼다**에 더 가깝습니다.

직관적으로는 다음과 같이 생각할 수 있습니다.

`x* = μX.(i_d ⊔ F_θ(X))`

여기서

- `i_d`
  - data가 올린 seed fact
- `F_θ`
  - spec/DSL이 컴파일된 operator
- `⊔`
  - 현재 상태와 새 사실을 합치는 누적 연산
- `μ`
  - 더 이상 새 사실이 생기지 않을 때까지 반복 적용한 최소 고정점

중요한 점은,
이 관점에선 중심이 pass 순서가 아니라
**새 판단 사실이 더 생기느냐 아니냐** 입니다.

---

## monotone core

코어에서는 가능한 한 모노토닉하게 움직이는 것이 좋습니다.

즉 이미 알게 된 사실을 함부로 지우기보다,
새 fact를 append하는 방향으로 가는 것입니다.

예를 들면:

- proposal 추가
- evidence 추가
- provenance edge 추가
- hazard open
- hazard discharge를 기록하는 새 사실 추가

이렇게 하면 코어는 “무엇을 알게 되었는가”를 누적하는 쪽에 집중할 수 있습니다.

현재 judgment vocabulary가 append-only 성격을 강하게 가지는 이유도 여기에 있습니다.

---

## thin non-monotonic shell

selection과 commit은 코어와 똑같이 다룰 수 없는 부분이 있습니다.

예:
- 대표 후보를 하나로 정해야 한다
- review로 보낼지 결정해야 한다
- public row를 열지 막을지 판단해야 한다

이 부분까지 전부 코어 mutation으로 섞어 버리면 구조가 다시 커집니다.

그래서 장기적으로는 이 부분을
**얇은 비모노토닉 껍질**로 남기는 것이 좋습니다.

### frontier / representative

candidate 전체를 바로 지워 버리기보다,
candidate summary 사이의 dominance를 보고 frontier를 계산합니다.

이 관점에선:

- 단일 winner가 있으면 자동 선택 가능
- frontier가 여러 개면 review가 필요할 수 있음
- 탈락 후보는 “삭제”보다 residue/비대표 상태로 남김

현재 `CandidateSummary`, `frontier`, `winner_or_none`은 이 방향의 초기 형태입니다.

### commit barrier

public state는 단순 row 생성과 다릅니다.

장기적으로 public row는 다음 같은 조건을 통과해야 합니다.

- 현재 선택이 fresh한가
- blocking hazard가 남아 있지 않은가
- provenance가 충분한가
- policy가 merge를 허용하는가

현재 `DraftSnapshot`, `CommitSpec`, `committable()`은 이 barrier vocabulary를 이미 제공합니다.

---

## public row는 partial projection

장기 구조에서 public row는 source of truth가 아닙니다.

source of truth에 더 가까운 것은 judgment state와 receipt log입니다.
public row는 그 상태에서 commit barrier를 통과한 결과를
밖으로 내보내는 **projection** 입니다.

이 관점이 중요한 이유는 다음과 같습니다.

1. emit이 본체 mutation이 아니라 materialization이 된다.
2. draft/review/public/explanation을 같은 코어의 다른 view로 다룰 수 있다.
3. 왜 merge는 hold인데 row는 보일 수 있는지 설명하기 쉬워진다.

현재 `ProjectionSpec`과 `comp.views.public` helper는 이 방향의 초기 구현입니다.

---

## incremental / delta 관점

장기적으로는 dirty-driven recomputation도
이 코어 의미론 위에서 설명하는 것이 좋습니다.

즉 “어디를 다시 돌릴 것인가”를 ad-hoc하게 관리하기보다,
변화량이 judgment state에 어떤 새 사실을 추가하는지,
그리고 어떤 bundle/frontier/commit barrier가 영향을 받는지로 설명하는 쪽이 더 자연스럽습니다.

이 문서에서 중요한 점은 특정 알고리즘을 고정하는 것이 아니라,
incremental 실행도 결국
**동일한 judgment state 위의 증분 고정점 계산**으로 본다는 점입니다.

---

## 현재 레포와의 연결점

현재 레포는 아직 이 의미론을 본류 실행 모델로 쓰지 않습니다.

대신 다음처럼 부분적으로 연결되어 있습니다.

- `current-pipeline.md`
  - 실제 본류는 staged pass chain
- `RepairPass`
  - selection 관련 상태와 receipt를 계산하는 bridge
- `comp.views.public`
  - public projection helper 제공
- `GovernancePass`
  - barrier/receipt vocabulary 일부 사용
- `comp.compat.adapters`
  - legacy artifact를 judgment vocabulary로 번역

즉 지금 레포는 완전한 fixpoint runtime은 아니지만,
이 문서가 설명하는 코어 의미론을 향해 vocabulary와 helper를 미리 세운 상태입니다.

---

## 이 문서가 고정하는 것과 고정하지 않는 것

### 이 문서가 고정하는 것

- `comp`의 장기 설명 중심은 row-first가 아니라 judgment-first 라는 점
- data와 spec이 같은 코어에서 만난다는 점
- selection/commit은 얇은 shell로 남겨야 한다는 점
- public row는 projection이라는 점

### 이 문서가 아직 고정하지 않는 것

- 최종 lattice 좌표의 정확한 분해
- obligation/review lifecycle의 정식 규칙
- delta runtime의 구체 알고리즘
- 모든 rule family의 최종 lowering 형식

즉 이 문서는 구현 세부를 잠그는 문서가 아니라,
**장기 구조를 설명하는 최소 의미론**을 고정하는 문서입니다.

---

## 요약

`comp`를 장기적으로 가장 간단하게 설명하면 이렇습니다.

- data는 seed fact를 올리고
- spec은 compiled operator로 내려오고
- core는 judgment state 위에서 고정점을 향해 fact를 누적하고
- selection과 commit은 얇은 shell로 남고
- public row는 barrier를 통과한 projection으로만 나타난다

즉 `comp`의 장기 본체는 pass 묶음이 아니라,
**하나의 judgment core semantics** 입니다.
