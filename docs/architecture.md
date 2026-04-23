# Architecture

## 한 줄 설명

`comp`는 ESGDL 기반의 **실험적 evidence compiler**이다.

이 레포는 raw fragment를 곧바로 정답 row로 바꾸는 도구라기보다,
후보·근거·충돌·정책을 축적한 뒤 정당한 public row만 안전하게 승격하는 구조를 목표로 한다.

---

## 현재 구조

현재 본류 실행 모델은 **stage pipeline**이다.

```text
LexPass
→ ParsePass
→ ScopeResolutionPass
→ InferencePass
→ SemanticPass
→ RepairPass
→ EmitPass
→ GovernancePass
→ CalculationPass
```

이 구조는 현재 레포의 주 실행 경로이며,
실제 runner는 이 pass chain을 따라 `CompileArtifacts`를 갱신한다.

핵심 산출물은 다음과 같다.

- fragments
- tokens
- claims
- frames
- rows
- calculations
- diagnostics
- merge_log
- event_log
- commit_log

즉 현재 구조는 **하나의 artifact container를 단계별로 정제하는 staged compiler**로 이해하는 것이 가장 정확하다.

---

## 장기 구조

장기적으로 `comp`는 단순 pass chain을 넘어
**judgment-first architecture**로 이동하는 것을 목표로 한다.

핵심 생각은 다음과 같다.

1. row를 최상위 본체로 두지 않는다.
2. candidate / evidence / hazard / provenance를 append-only judgment vocabulary로 다룬다.
3. representative selection은 frontier 계산으로 설명한다.
4. public row는 commit barrier를 통과한 projection만 허용한다.
5. data와 spec을 같은 판정 어휘로 본다.

즉 목표 구조는 대략 다음과 같다.

```text
raw input
→ seed facts
→ monotone transfer / fixpoint
→ frontier / winner selection
→ commit barrier
→ public projection
```

---

## 현재 레포의 실제 상태

현재 레포는 “완전히 새 구조로 넘어간 상태”는 아니다.

더 정확히는:

- 공개 정체성은 README와 pyproject를 통해 정리되었다.
- `comp.judgment`, `comp.views`, `comp.compat`가 실제 코드로 들어왔다.
- 그러나 메인 러너와 주 pass 체인은 아직 기존 staged pipeline이 본류다.
- 일부 `comp.pipeline.*` 모듈은 façade 또는 legacy wrapper 성격을 가진다.

즉 현재 상태는 **legacy pipeline 위에 새 judgment vocabulary가 부분적으로 스며든 bridge 단계**로 보는 것이 맞다.

---

## 세 층으로 보는 현재 레포

### 1. 현재 본류
- `pipeline_runner.py`
- 기존 pass chain
- `CompileArtifacts`

### 2. 새 의미층
- `comp.judgment`
- `comp.views`
- `comp.compat`

### 3. 이행 표면
- `comp.pipeline.*`
- 패키지 공개 surface
- legacy와 새 구조를 동시에 연결하는 bridge

---

## 이 구조를 이렇게 두는 이유

지금 레포는 두 가지 요구를 동시에 만족해야 한다.

1. 현재 동작하는 staged pipeline을 유지해야 한다.
2. 장기적으로 judgment-first 구조로 갈 수 있는 의미 축을 먼저 세워야 한다.

한 번에 전면 재작성하면 현재 테스트, artifact 계약, existing flow가 무너질 수 있다.
반대로 새 구조를 전혀 도입하지 않으면 emit / governance / selection을 더 이상 설명 가능하게 만들기 어렵다.

따라서 지금 단계의 올바른 구조는:

- 현재 파이프라인을 유지하되
- selection / projection / commit vocabulary를 먼저 분리하고
- 이후 점진적으로 본류를 judgment core 쪽으로 이동하는 것

이다.

---

## 핵심 설계 원칙

1. **row-first가 아니라 judgment-first**
2. **append-only core**
3. **draft와 public row의 분리**
4. **emit은 source of truth가 아니라 projection**
5. **selection / commit의 이유를 receipt로 남김**
6. **spec과 data를 같은 판정 어휘로 설명**

---

## 다음 문서

- 현재 실제 실행 흐름: `current-pipeline.md`
- judgment core의 개념과 현재 연결점: `judgment-core.md`
- 앞으로의 정리 순서: `migration-plan.md`
