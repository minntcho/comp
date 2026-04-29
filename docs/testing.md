# Testing

이 문서는 `comp`의 테스트가 **무엇을 보호하는지** 설명한다.

중요:
여기서는 “pytest를 어떻게 실행하나”보다
**각 테스트가 어떤 구조적 약속을 지키는가**를 중심으로 적는다.

---

## 테스트의 역할

`comp`는 단순 함수 하나의 입력/출력만 보는 레포가 아니다.

이 레포는 다음을 동시에 보존해야 한다.

- artifact 계약
- staged pipeline 결과 일관성
- compiled path와 기존 path의 동치성
- selection / repair / governance의 안정성
- e2e 결과의 회귀 방지

즉 테스트는 “값이 맞는가”만이 아니라
**현재 구조가 깨졌는가**를 잡는 장치다.

---

## 테스트 층위

현재 테스트는 크게 네 층으로 나눠 볼 수 있다.

### 1. Artifact contract 테스트
목적:
- artifact 자료형과 helper의 계약이 깨지지 않는지 확인

대표적으로 보는 것:
- frame diagnostics가 `DiagnosticArtifact`인지
- helper가 예상 타입 외 입력에 fail-fast 하는지
- repair 이후 runtime 상태가 채워지는지
- row error code가 frame diagnostics와 일치하는지

이 층은 `artifacts.py`의 의미를 보호한다.

즉:
“지금 구조에서 artifact가 무엇을 약속하는가”를 지키는 테스트다.

---

### 2. Stage smoke / golden 테스트
목적:
- 특정 stage까지의 산출물이 기존 기대값과 같은지 확인

예:
- `RepairPass` 직후 snapshot이 golden과 같은지 비교

이 층은
특정 pass를 고쳤을 때 중간 산출물이 의도치 않게 바뀌는지 잡는다.

즉:
“현재 pipeline의 중간 상태”를 보호하는 테스트다.

---

### 3. Compiled runner parity 테스트
목적:
- compiled path가 기존 pipeline path와 같은 결과를 내는지 확인

핵심 질문:
- `CompiledProgramSpec`로 내려간 경로가
  기존 spec 실행과 의미적으로 같은가

이 층은 매우 중요하다.
왜냐하면 이 레포는 binder / compiled path를 강화하고 있기 때문이다.

즉:
“새 실행 경로가 기존 경로를 깨지 않고 같은 의미를 유지하는가”를 보호한다.

---

### 4. End-to-end golden 테스트
목적:
- 실제 케이스 전체 실행 결과가 golden과 같은지 확인

이 층은 다음을 함께 본다.

- fragments
- tokens
- claims
- frames
- rows
- calculations
- diagnostics
- merge decisions

즉:
“레포 전체가 지금 어떤 동작을 하는가”를 보호하는 가장 넓은 테스트다.

---

## 테스트가 보호하는 핵심 불변조건

### 1. Artifact shape가 갑자기 바뀌지 않는다
필드 이름, 타입, 의미가 조용히 깨지면 안 된다.

### 2. Repair의 결과는 설명 가능해야 한다
score, iteration, termination reason 같은 runtime 값이 비어 있으면 안 된다.

### 3. Compiled path는 기존 path와 동치여야 한다
compiled route를 강화하더라도 의미가 바뀌면 안 된다.

### 4. Public row와 governance 결과는 회귀하면 안 된다
row/error/merge/calculation 결과가 무심코 바뀌면 안 된다.

---

## 테스트를 읽을 때의 기준

새 기능을 넣거나 구조를 바꿀 때는
아래 순서로 테스트를 보는 게 좋다.

### 구조만 바꾼 경우
1. artifact contract
2. stage smoke
3. e2e golden

### binder / compiled path를 건드린 경우
1. compiled runner parity
2. e2e golden

### repair / selection / governance를 건드린 경우
1. repair stage smoke
2. artifact contract
3. e2e golden

---

## 앞으로 더 필요해질 테스트

현재 구조가 judgment-first 쪽으로 더 이동하면,
다음 테스트가 더 중요해질 가능성이 크다.

### 1. judgment core 단위 테스트
- `Fact`
- `JudgmentState`
- `FixpointEngine`
- `frontier`
- `committable`

### 2. receipt 테스트
- selection receipt가 현재 slot 상태를 제대로 반영하는지
- commit receipt가 barrier snapshot을 제대로 담는지

### 3. projection 테스트
- public projection이 source of truth를 왜곡하지 않는지
- emit/view helper가 같은 입력에 대해 안정적으로 같은 결과를 내는지

---

## 문서의 결론

`comp`의 테스트는 단순히 “정답 값 비교”가 아니다.

이 레포에서 테스트는 다음을 보호한다.

- 현재 staged pipeline의 의미
- artifact 계약
- compiled path의 동치성
- judgment-first 구조로 가는 이행 과정의 안전성

즉 테스트는 결과 검증 도구이면서 동시에
**현재 아키텍처의 경계와 약속을 고정하는 장치**다.
