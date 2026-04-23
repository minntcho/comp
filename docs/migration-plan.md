# Migration Plan

이 문서는 `comp`의 구조 이행 작업을 추적한다.

중요:
이 문서는 추상 설계 문서가 아니다.
PR 단위로 무엇이 이미 들어왔고, 무엇이 아직 façade/bridge 상태인지,
그리고 다음에 무엇을 실제로 옮길지를 적는 문서다.

---

## 현재 상태 요약

현재 레포는 다음 세 층이 공존한다.

### 1. legacy 본류
- top-level 모듈
- staged pass 실행
- `pipeline_runner.py` 중심 구조

### 2. 새 공개 표면
- `comp.*` 패키지
- `README.md`
- `pyproject.toml`

### 3. bridge / adapter 층
- `comp.compat`
- `comp.views`
- `comp.judgment`
- 일부 `comp.pipeline.*` façade

즉 현재 상태는 **정리 완료**가 아니라 **의도적 bridge 단계**다.

---

## 이미 들어온 것

### 패키지 표면
- `pyproject.toml`
- `comp.dsl`
- `comp.pipeline`
- `comp.eval`
- `comp.builtins`
- `comp.compat`
- `comp.judgment`
- `comp.views`

### 공개 정체성
- 한국어 README
- judgment-first 방향 명시
- experimental 상태 명시

### 새 구조의 실제 코드
- `Fact`, `JudgmentState`
- `FixpointEngine`
- `frontier`
- `committable`
- public projection helpers
- selection / commit adapter

---

## 아직 façade 또는 wrapper인 부분

### `comp.pipeline.*`
일부 모듈은 아직 실제 구현체가 아니라 legacy top-level 모듈 re-export다.

예:
- `comp.pipeline.repair`

### `comp.compat.*`
일부 호환 모듈은 실제 이행을 위한 thin wrapper다.

예:
- `comp.compat.artifacts`

### main runner
주 실행은 아직 top-level `pipeline_runner.py` 중심이다.

즉 새 패키지가 생겼지만,
본류 import 경로와 실제 구현체 이동은 아직 중간 단계다.

---

## 구조 debt

현재 가장 중요한 debt는 다음 네 가지다.

1. **루트 import 의존**
   - 본류 실행이 아직 top-level 모듈 중심이다.

2. **façade 잔존**
   - `comp.pipeline.*` 일부가 공개 표면만 제공하고 실제 구현은 legacy에 남아 있다.

3. **row 중심 mutation**
   - emit / governance / commit이 아직 완전히 ledger/receipt 중심으로 넘어가지 않았다.

4. **judgment core의 본류 미흡수**
   - judgment vocabulary는 들어왔지만 main executor는 아직 stage pipeline이다.

---

## 다음 PR 우선순위

### PR-A: import surface 정리
목표:
- 테스트와 문서 기준 import를 `comp.*`로 수렴
- 새 package surface를 정식 경로로 확정

완료 기준:
- 새 코드 예제와 테스트에서 legacy import를 줄임

---

### PR-B: façade 제거
목표:
- `comp.pipeline.*` 내부에서 실제 구현체를 패키지 안으로 이동
- thin re-export 감소

완료 기준:
- `importlib` re-export 모듈 축소
- 실제 구현이 패키지 내부로 이동

---

### PR-C: emit / governance 경계 정리
목표:
- emit을 projection으로 더 명확히 분리
- governance를 barrier / receipt 중심으로 더 정리

완료 기준:
- row mutation보다 receipt/log 중심 설명이 더 자연스러워짐

---

### PR-D: judgment core 흡수 시작
목표:
- 일부 규칙 또는 selection 흐름을 judgment program 관점으로 직접 표현
- adapter 아닌 실제 본류 흡수 시작

완료 기준:
- judgment core가 설명용 보조층이 아니라 일부 실행 경로를 직접 담당

---

## 하지 말아야 할 것

1. 한 번에 전면 재작성
2. façade를 오래 방치한 채 패키지 이름만 늘리기
3. README/문서만 새 구조를 말하고 본류 코드는 그대로 두기
4. judgment core를 실제 실행 흡수 없이 “좋은 미래 설계”로만 방치하기

---

## 최종 목표

장기적으로는 다음 상태를 목표로 한다.

- 공개 import surface는 `comp.*`로 통일
- legacy top-level 모듈 제거 또는 최소화
- selection / commit / projection 책임 분리
- judgment core가 본류 실행 모델 일부를 직접 담당
- receipt / ledger 중심 설명 가능성 강화

즉 목표는 단순히 “폴더 정리된 레포”가 아니라,
**현재 pipeline과 장기 judgment 구조가 하나의 설명 체계로 수렴된 레포**다.
