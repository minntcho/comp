# Migration Checklist

이 문서는 `comp` 구조 이행의 **실행 체크리스트**입니다.

목표:
- 설계 논의를 작업 가능한 PR 단위로 고정한다.
- “진행됨/미진행” 상태를 코드 기준으로 추적한다.
- 이행 중 회귀를 빠르게 감지한다.

---

## 0) 운영 규칙

- 단위는 반드시 **PR**로 끊는다.
- 각 PR은 “완료 조건(acceptance criteria)”를 먼저 만족해야 한다.
- 한 PR에서 import 정리 + 구조 이동 + 의미 변경을 동시에 하지 않는다.
- 회귀가 발생하면 즉시 롤백 가능하도록 shim/adapter를 단계적으로 유지한다.
- stacked PR를 허용한다.
- stacked PR은 반드시 base branch를 PR 본문에 명시한다.
- 각 stacked PR은 base가 merge된 뒤 독립적으로 검토 가능해야 한다.
- stacked PR에서도 의미 변경은 packaging/migration PR과 분리한다.

---

## 1) Done / In flight / Now / Next / Later

### Done / In flight

- [x] façade surface 구축 및 package 공개 표면(`comp.*`) 정리 착수
- [x] internal import convergence 일부 진행
- [x] actual relocate 시작
  - builtins/eval 일부 leaf 모듈 패키지 경로 정리

### Now (즉시)

#### A-track: import convergence
- [ ] **PR-A1: internal import convergence**
  - 신규/수정 코드 import를 `comp.*` 중심으로 수렴
  - legacy import 사용은 compat/bridge 문맥으로 제한

- [ ] **PR-A2: eager import / cycle 차단**
  - `comp.__init__` / `comp.runner` / `comp.compat.*` / legacy runner 경로의 eager import를 점검
  - module import 단계에서 상호 재귀 경로 제거

- [ ] **PR-A3: DSL path 정합성 복구**
  - `comp.eval.compiled_expr`가 참조하는 DSL 경로를 실제 패키지 구조와 일치시킴

#### R-track: actual relocate
- [x] **PR-R1a: relocate `esg_builtins`**
- [x] **PR-R1b: relocate `rule_builtins`**
- [x] **PR-R1c: relocate `expr_eval`**
- [x] **PR-R1d: relocate `compiled_expr_eval`**
- [ ] **PR-R1e: relocate `lex_eval`**
- [ ] **PR-R1f: relocate `source_eval`**

### Next (다음)

#### R-track: actual relocate 확장
- [ ] **PR-R2: relocate runtime/artifacts/compiled_spec leaf-safe pieces**
- [ ] **PR-R3: relocate runner-adjacent modules**

#### Architecture track (초기)
- [ ] **PR-C1: emit/governance boundary 정리 시작**
  - emit projection 경계와 governance barrier 경계 분리

### Later (후속)

#### B-track: façade 축소 기준 수립 후 제거
- [ ] **PR-B: façade 축소 기준 수립**
- [ ] **PR-B1: facade thinness audit**
- [ ] **PR-B2: facade 제거 후보 선정 및 점진 제거**

#### Architecture track (본격)
- [ ] **PR-D: judgment core 본류 흡수**
  - selection/commit 일부 실행을 judgment program+engine 경로로 직접 전환

#### Legacy surface 축소
- [ ] **PR-E: legacy top-level 모듈 단계적 축소**

---

## 2) 트랙별 완료 조건 (Acceptance Criteria)

### A-track (import convergence)

- [ ] 신규/수정 코드가 `comp.*` import를 사용한다.
- [ ] 문서 예제가 `comp.*` 기준이다.
- [ ] import cycle이 사라져 test collection이 진행된다.
- [ ] `ModuleNotFoundError` 경로 불일치가 해소된다.

### R-track (relocation)

- [ ] package 쪽 파일이 실제 구현을 가진다.
- [ ] top-level legacy 모듈은 thin wrapper만 남는다.
- [ ] package import와 legacy import가 같은 객체를 가리킨다.
- [ ] smoke/parity 테스트 1개 이상으로 identity를 확인한다.
- [ ] 의미 변경은 없다.

### B-track (façade 축소)

- [ ] facade thinness 기준(허용/제거)을 문서화했다.
- [ ] 제거 후보별 영향도(테스트/사용자 경로)를 기록했다.
- [ ] 공개 API를 유지한 채 thin wrapper 수가 감소한다.

### Architecture track

- [ ] emit가 row source-of-truth가 아니라 projection 경계로 설명 가능하다.
- [ ] governance가 barrier/receipt 중심으로 추적 가능하다.
- [ ] judgment core 경로가 일부 실제 실행을 담당한다.

---

## 3) Packaging/Migration Track vs Architecture Track

### Packaging / Migration track
- import convergence
- actual relocate
- façade thinness 관리
- legacy top-level shim 축소

### Architecture track
- emit/governance boundary refactor
- projection/view 정리
- judgment core 본류 흡수
- fixpoint execution 본류화

---

## 4) 리스크 / 롤백 전략

- import 정리 PR에서 API break가 나면 shim 파일로 즉시 복구한다.
- 구조 이동 PR에서 동작 회귀가 나면 구현만 되돌리고 공개 surface는 유지한다.
- judgment 흡수 PR은 항상 parity 테스트와 함께 머지한다.

---

## 5) 검증 체크 커맨드

> 아래는 PR마다 최소 1회 실행한다. (변경 영역 우선)

- `pytest -q`
- `pytest -q tests/test_runner_package_facades.py tests/test_pipeline_package_facades.py`
- `pytest -q tests/test_eval_module_facades.py`
- `pytest -q tests/test_esg_builtins_package_location.py tests/test_rule_builtins_package_location.py`
- `pytest -q tests/test_expr_eval_package_location.py tests/test_compiled_expr_eval_package_location.py`

---

## 6) 진행 로그

### 2026-04-23

- 체크리스트 문서 생성.
- 피드백 반영:
  - `Done / In flight` 섹션 추가
  - A-track(import convergence) 세분화
  - R-track(actual relocate) 추가
  - B-track을 “제거”가 아니라 “축소 기준 수립” 중심으로 조정
  - 검증 커맨드를 현재 smoke/parity 축 기준으로 갱신
- 다음 액션:
  - PR-A1/A2/A3 계속 진행
  - PR-R1 잔여 leaf(`lex_eval`, `source_eval`) 마감
  - 이후 PR-R2(runtime/artifacts/compiled_spec)로 확장
