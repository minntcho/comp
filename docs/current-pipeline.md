# Current Pipeline

이 문서는 **현재 레포에서 실제로 실행되는 staged pipeline**만 설명한다.

여기서는 장기 judgment 설계의 이상형을 섞지 않는다.
지금 코드가 실제로 무엇을 하고 있는가만 적는다.

---

## 실행 순서

현재 기본 실행 순서는 다음과 같다.

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

필요하면 `semantic_post`가 `RepairPass` 뒤에 추가될 수 있다.

---

## 실행 단위

실행의 중심 객체는 `CompileArtifacts`다.

이 객체는 다음 산출물을 단계별로 들고 간다.

- fragments
- tokens
- claims
- frames
- rows
- calculations
- diagnostics
- event_log
- commit_log
- merge_log

즉 현재 구조의 핵심은
**하나의 artifact container를 각 pass가 순차적으로 갱신하는 방식**이다.

---

## 단계별 역할

### 1. LexPass
입력 fragment에서 token occurrence를 만든다.

결과:
- `artifacts.tokens`

### 2. ParsePass
token과 parser rule을 바탕으로 claim / partial frame을 만든다.

결과:
- `artifacts.claims`
- `artifacts.frames`

### 3. ScopeResolutionPass
context와 scope 규칙을 사용해 slot 후보를 좁히거나 상속/보완한다.

결과:
- frame 내부 slot 상태 보정
- claim 상태 일부 조정

### 4. InferencePass
명시적으로 보이지 않는 값도 규칙에 따라 후보로 추가한다.

결과:
- claim 추가
- inferred candidate 생성

### 5. SemanticPass
constraint / diagnostic / rule builtin 평가를 통해 warning/error를 쌓는다.

결과:
- frame diagnostics
- artifact diagnostics

### 6. RepairPass
slot별 active/shadow/frozen/rejected를 재정렬하고,
frame-level score / stability / commit 판정을 계산한다.

결과:
- slot lifecycle 정리
- frame status 정리
- frame runtime 값 갱신
- selection receipt 저장

### 7. EmitPass
committed frame을 대상으로 canonical row를 materialize한다.

중요:
- 여기서는 row를 projection처럼 다루기 시작했지만,
- 현재 구조상 row는 여전히 `artifacts.rows`에 materialize된다.

### 8. GovernancePass
row 단위 policy와 commit barrier를 보고 merge/hold/skip을 결정한다.

결과:
- `merge_log`
- `event_log`
- `commit_log`
- row status 일부 변경

### 9. CalculationPass
merge 가능한 row를 기준으로 calculation을 수행한다.

결과:
- `artifacts.calculations`

---

## 현재 구조의 장점

1. 실행 순서가 명확하다.
2. artifact 기반이라 디버깅과 golden test가 쉽다.
3. 단계별 책임을 나눠보기 쉽다.
4. compiled runner parity 테스트를 붙이기 좋다.

---

## 현재 구조의 약점

1. row가 비교적 이른 시점에 실체처럼 등장한다.
2. selection / projection / governance가 stage 경계에 걸쳐 있다.
3. emit / governance / calculation이 장기 구조 기준으로는 아직 완전히 분리되지 않았다.
4. judgment-first 구조로 가기엔 현재 artifact mutation 중심 흐름이 강하다.

---

## 현재 문서의 범위 바깥

이 문서에서는 다음을 자세히 다루지 않는다.

- `Fact`, `JudgmentState`, `FixpointEngine`
- frontier 기반 candidate selection
- commit barrier의 장기 정식 모델
- spec/data를 같은 judgment language로 다루는 구조

그 내용은 `judgment-core.md`에서 다룬다.
