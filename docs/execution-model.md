# Execution Model

이 문서는 `comp`의 **목표 실행 모델**을 설명합니다.

중요:
현재 실제로 돌아가는 pass chain은 `current-pipeline.md`가 설명합니다.
이 문서는 그 문서를 덮어쓰지 않습니다.

여기서는 다음을 다룹니다.

- 왜 장기적으로 pass 목록만으로는 구조를 설명하기 어려운가
- 목표 실행 모델에서 어떤 엔진 경계가 중요한가
- 현재 pass를 그 목표 모델에 어떻게 대응시킬 수 있는가
- migration 과정에서 무엇을 섞지 말아야 하는가

---

## 왜 execution model 문서가 따로 필요한가

현재 레포는 staged pipeline으로 동작합니다.
그 자체는 지금 단계에서 맞는 구조입니다.

하지만 장기적으로 `comp`를 설명할 때,
pass 이름만 계속 늘어놓는 방식에는 한계가 있습니다.

왜냐하면 `comp`의 중요한 질문은 다음이기 때문입니다.

- 후보와 근거는 어디서 누적되는가
- 대표선출은 어디서 일어나는가
- public 승격은 어디서 막히거나 허용되는가
- emit/view는 core mutation인가 projection인가

즉 장기적으로는
“무슨 pass가 몇 번째에 돈다”보다
**어떤 엔진이 어떤 책임을 가진다**가 더 중요해집니다.

---

## 목표 실행 모델의 큰 그림

장기적으로는 다음 실행 모델이 더 자연스럽습니다.

```text
frontend
→ saturation
→ arbitration
→ commit
→ post-commit / views
```

여기서 핵심은 세 엔진입니다.

- `saturation`
- `arbitration`
- `commit`

frontend와 post-commit/view는 중요하지만,
핵심 판단 구조는 저 세 엔진이 나눠 갖는 편이 좋습니다.

---

## 1. frontend

frontend는 raw input를 judgment world로 올리는 앞단입니다.

대표적으로는 다음 일을 합니다.

- fragment 준비
- token 추출
- parser 적용
- 초기 claim/frame 생성

즉 frontend의 역할은 아직 최종 판단을 내리는 것이 아니라,
**판정 가능한 seed를 만드는 것** 입니다.

---

## 2. saturation

`saturation`은 가능한 한 모노토닉하게 fact를 누적하는 엔진입니다.

대표적으로는 다음 역할을 맡습니다.

- proposal 추가
- evidence 추가
- provenance 확장
- infer rule 적용
- semantic constraint/diagnostic 반영
- hazard open / discharge 관련 사실 누적

직관적으로는,
“새 사실을 계속 더해 보고 더 이상 추가될 것이 없을 때까지 간다”는 쪽에 가깝습니다.

장기적으로는 이 엔진이 judgment state를 고정점 쪽으로 밀어가는 본체가 됩니다.

---

## 3. arbitration

`arbitration`은 후보를 대표선출 관점에서 정리하는 엔진입니다.

여기서는 다음 질문을 다룹니다.

- 어떤 후보들이 같은 bundle에서 경쟁하는가
- dominance/frontier 기준으로 보면 최대 후보는 누구인가
- single winner인가, review가 필요한가
- residue/shadow/rejected 상태는 어떻게 설명되는가
- stale recheck가 필요한가

즉 arbitration은 “사실을 더 쌓는” 엔진이라기보다,
**누적된 판단 세계를 보고 대표선출 상태를 정리하는 엔진** 입니다.

현재 레포에선 이 역할이 상당 부분 `RepairPass`에 섞여 있습니다.

---

## 4. commit

`commit`은 draft를 public state로 승격시킬지 판단하는 엔진입니다.

중심 질문은 다음과 같습니다.

- 현재 선택이 fresh한가
- blocking hazard가 남아 있는가
- provenance가 충분한가
- policy가 merge를 허용하는가
- public ledger에 append할 수 있는가

즉 commit은 row를 “만드는” 단계라기보다,
**이미 형성된 draft를 public state로 인정할 수 있는지 검사하는 barrier 단계** 입니다.

현재 레포에선 `GovernancePass`가 이 역할의 일부를 맡고 있습니다.

---

## 5. post-commit / views

public state 이후에는 두 가지가 갈립니다.

### post-commit

- calculation
- external apply/effect
- downstream derivation

### views

- draft view
- review view
- public export view
- explanation view

중요:
이 둘은 core judgment mutation과 분리되어야 합니다.
특히 emit/public row materialization은 장기적으로 view 쪽에 더 가깝습니다.

---

## 현재 pass와 목표 엔진의 대응

현재 레포를 목표 실행 모델에 대응시키면 대략 다음과 같이 볼 수 있습니다.

### `LexPass`, `ParsePass`
- frontend
- raw를 token/claim/frame seed로 올리는 역할

### `ScopeResolutionPass`, `InferencePass`, `SemanticPass`
- saturation 쪽에 가까움
- 후보/근거/diagnostic/hazard 관련 상태를 누적

### `RepairPass`
- arbitration + control이 섞인 상태
- selection, freeze/reject, stability, receipt가 한 곳에 뭉쳐 있음

### `EmitPass`
- 장기적으로는 view/materialization으로 더 내려갈 부분이 큼
- 현재는 row를 materialize하는 bridge 역할

### `GovernancePass`
- commit barrier 쪽에 가까움
- hold/merge 판단과 commit receipt를 다룸

### `CalculationPass`
- post-commit 쪽에 가까움
- committed/mergeable 상태 이후의 계산을 맡음

즉 현재 pipeline은 완전히 잘못된 구조가 아니라,
장기적으로는 다른 엔진 경계로 다시 묶여야 하는 **1세대 분해**라고 보는 것이 맞습니다.

---

## migration에서 지켜야 할 것

execution model을 바꾼다고 해서,
한 번에 본류를 뒤집는 것은 좋지 않습니다.

특히 다음을 섞지 않는 것이 중요합니다.

1. packaging 이동과 의미 변경
2. façade 제거와 selection semantics 변경
3. runtime 재배치와 golden/parity 붕괴

즉 장기 execution model은 먼저 문서와 vocabulary로 세우고,
실제 본류 이동은 adapter와 parity를 유지하면서 점진적으로 하는 편이 맞습니다.

---

## 현재 레포의 위치

현재 레포는 아직 목표 execution model을 직접 실행하지 않습니다.

더 정확히는:

- 본류는 staged pipeline이다
- 일부 judgment vocabulary는 이미 들어와 있다
- selection/commit/projection helper도 부분적으로 들어와 있다
- 그러나 메인 러너가 `saturation → arbitration → commit`을 직접 돌리는 구조는 아니다

즉 지금은 목표 execution model로 가기 위한 bridge 단계입니다.

---

## 요약

장기적으로 `comp`를 가장 자연스럽게 설명하는 실행 모델은:

- frontend
- saturation
- arbitration
- commit
- post-commit / views

의 구조입니다.

이 관점에서 보면,
현재 pass chain은 버려야 할 것이 아니라
**앞으로 다른 엔진 경계로 재정렬될 1세대 구현** 입니다.
