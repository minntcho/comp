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

## 1) Done / Bridge / Now / Next / Later

### Done

#### Docs / public surface
- [x] 한국어 README와 `pyproject.toml`을 통해 공개 정체성 정리
- [x] `docs/` 내부 지도 추가
- [x] judgment language / core semantics / spec pipeline / execution model / views-ledger 문서 추가
- [x] package 공개 표면(`comp.*`) 구축 착수
- [x] runner / pipeline / eval / builtins façade surface 구축
- [x] `AGENTS.md`에 issue / PR / checklist 기반 agent 운영 규칙 추가
- [x] `AGENTS.md`에 병렬 작업용 `area:*` / `flow:*` label 축 추가

#### A-track: import convergence
- [x] **PR-A1: internal import convergence**
  - `scope_resolution_pass.py` / `inference_pass.py` / `semantic_pass.py` / `calculation_pass.py`가 `comp.*` 경로를 우선 사용하도록 정렬
  - relocation 이후 import를 package 중심으로 수렴
- [x] **PR-A2: eager import / cycle 차단**
  - `comp.__init__`에서 runner export를 lazy resolution(`__getattr__`)로 전환
  - `import comp` 시점에 legacy runner bridge가 eager import되지 않음을 smoke test로 고정
- [x] **PR-A3: DSL path 정합성 복구**
  - `comp.eval.compiled_expr` / `comp.eval.lex` / `comp.eval.source_module` / `comp.dsl.compiled_spec`가 `comp.dsl.*` 경로를 참조
  - 신규 package implementation은 가능한 한 `comp.*` import를 사용

#### R-track: actual relocate
- [x] **PR-R1a: relocate `esg_builtins`**
- [x] **PR-R1b: relocate `rule_builtins`**
- [x] **PR-R1c: relocate `expr_eval`**
- [x] **PR-R1d: relocate `compiled_expr_eval`**
- [x] **PR-R1e: relocate `lex_eval`**
- [x] **PR-R1f: relocate `source_eval`**
- [x] **PR-R1g: relocate `rule_eval`**
- [x] **PR-R1h: relocate `ast_nodes`**
- [x] **PR-R1i: relocate `spec_nodes`**
- [x] **PR-R1j: relocate `lex_ir`**
- [x] **PR-R1k: relocate `source_ir`**
- [x] **PR-R1l: relocate `rule_ir`**
- [x] **PR-R2a: relocate `compiled_spec`**
- [x] **PR-R2b: relocate `runtime_env`**
  - `comp/runtime_env.py`가 실제 implementation을 소유
  - top-level `runtime_env.py`는 compatibility wrapper로 축소
  - package / legacy identity smoke test 추가
- [x] **PR-R2c: relocate `artifacts`**
  - `comp/artifacts.py`가 실제 implementation을 소유
  - top-level `artifacts.py`는 compatibility wrapper로 축소
  - `comp.compat.artifacts`는 package implementation을 참조
  - artifact identity / parity smoke test 추가
- [x] **PR-R3: relocate runner-adjacent modules**
  - `comp.pipeline_runner` / `comp.compiled_pipeline_runner`가 실제 runner implementation을 소유
  - top-level `pipeline_runner.py` / `compiled_pipeline_runner.py`는 compatibility wrapper로 축소
  - `comp.compat.pipeline_runner` / `comp.compat.compiled_pipeline_runner`는 package implementation을 참조
  - runner wrapper / package parity test 갱신

#### B-track: façade 축소 기준 수립
- [x] **PR-B0: facade inventory / thinness audit**
  - `docs/facade-inventory.md`에 public API facade / temporary migration bridge / legacy compatibility wrapper / bridge adapter 분류 추가
  - removal candidates를 기록하되 제거는 하지 않음
- [x] **PR-B1: facade thinness rule 문서화**
  - `docs/facade-thinness.md`에 wrapper 허용 패턴 / 금지 패턴 / classification별 규칙 추가
  - wrapper가 hidden behavior를 담지 못하도록 기준 고정

#### R/A bridge cleanup
- [x] **PR-R2d: package/compat imports after runtime/artifacts move**
  - runtime/artifacts relocation 이후 pass/runner-adjacent import를 package 경로 기준으로 정렬
  - behavior change 없이 import 경로만 정리

---

### Bridge state

현재 레포는 정리 완료 상태가 아니라 **의도적 bridge 단계**다.

- [ ] top-level legacy 모듈이 아직 배포 표면에 남아 있다.
- [ ] `runtime_env.py` / `artifacts.py` / `pipeline_runner.py` / `compiled_pipeline_runner.py`는 아직 top-level compatibility wrapper로 남아 있다.
- [ ] 일부 `comp.pipeline.*` 모듈은 여전히 thin wrapper 또는 legacy bridge다.
- [ ] `pyproject.toml`의 `py-modules`에는 legacy top-level 모듈들이 아직 포함되어 있다.

---

### Now (즉시)

#### R-track: pass implementation relocation
- [ ] **PR-R4: relocate pass implementation modules**
  - `*_pass.py` implementation을 package-owned modules로 점진 이동
  - `comp.pipeline.*` temporary bridges를 package implementation re-export로 재분류

#### Architecture track (초기)
- [ ] **PR-C1b: emit/governance boundary 코드 정리**
  - #73 docs boundary 정리 이후 코드에서 emit projection 경계와 governance barrier 경계를 명확히 분리
  - row materialization / commit decision / receipt append 책임을 코드 경계 기준으로 더 명확히 분리

---

### Next (다음)

#### Legacy surface 축소
- [ ] **PR-E: legacy top-level 모듈 단계적 축소**
  - package 경로가 충분히 안정된 뒤 top-level module surface를 줄임
  - 제거 전에는 deprecation / compatibility 방침을 먼저 정리

---

### Later (후속)

#### Architecture track (본격)
- [ ] **PR-D: judgment core 본류 흡수**
  - selection/commit 일부 실행을 judgment program+engine 경로로 직접 전환
  - adapter가 아니라 실제 실행 경로 일부를 judgment core가 담당

---

## 2) 트랙별 완료 조건 (Acceptance Criteria)

### A-track (import convergence)

- [ ] 신규/수정 코드가 `comp.*` import를 사용한다.
- [ ] 문서 예제가 `comp.*` 기준이다.
- [ ] import cycle이 사라져 test collection이 진행된다.
- [ ] `ModuleNotFoundError` 경로 불일치가 해소된다.
- [ ] legacy import는 compatibility wrapper 또는 bridge 문맥으로 제한된다.

### R-track (relocation)

- [ ] package 쪽 파일이 실제 구현을 가진다.
- [ ] top-level legacy 모듈은 thin wrapper만 남는다.
- [ ] package import와 legacy import가 같은 객체를 가리킨다.
- [ ] smoke/parity 테스트 1개 이상으로 identity를 확인한다.
- [ ] 의미 변경은 없다.
- [ ] relocation PR은 import convergence 또는 architecture change와 섞지 않는다.

### B-track (façade 축소)

- [x] facade thinness 기준(허용/제거)을 문서화했다.
- [x] 제거 후보별 영향도(테스트/사용자 경로)를 기록했다.
- [ ] 공개 API를 유지한 채 thin wrapper 수가 감소한다.
- [x] compatibility wrapper와 temporary bridge wrapper가 구분된다.

### Architecture track

- [ ] emit가 row source-of-truth가 아니라 projection 경계로 설명 가능하다.
- [ ] governance가 barrier/receipt 중심으로 추적 가능하다.
- [ ] judgment core 경로가 일부 실제 실행을 담당한다.
- [ ] architecture PR은 packaging relocation과 분리한다.

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
- runtime/artifacts relocation은 영향 범위가 넓으므로 작은 PR로 쪼갠다.
- runner-adjacent relocation은 반드시 package/legacy parity 테스트를 먼저 둔다.
- judgment 흡수 PR은 항상 parity 테스트와 함께 머지한다.

---

## 5) 검증 체크 커맨드

> 아래는 PR마다 최소 1회 실행한다. (변경 영역 우선)

### 전체 smoke
- `pytest -q`

### package / runner façade
- `pytest -q tests/test_package_smoke.py`
- `pytest -q tests/test_runner_package_facades.py tests/test_pipeline_package_facades.py`

### builtins relocation
- `pytest -q tests/test_esg_builtins_package_location.py tests/test_rule_builtins_package_location.py`

### eval relocation
- `pytest -q tests/test_expr_eval_package_location.py tests/test_compiled_expr_eval_package_location.py`
- `pytest -q tests/test_lex_eval_package_location.py tests/test_source_eval_package_location.py tests/test_rule_eval_package_location.py`

### DSL / IR relocation
- `pytest -q tests/test_ast_nodes_package_location.py tests/test_spec_nodes_package_location.py`
- `pytest -q tests/test_lex_ir_package_location.py tests/test_source_ir_package_location.py tests/test_rule_ir_package_location.py`
- `pytest -q tests/test_compiled_spec_package_location.py`

### runtime / artifacts relocation
- `pytest -q tests/test_runtime_env_package_location.py`
- `pytest -q tests/test_artifacts_package_location.py`
- `pytest -q tests/test_artifact_contract.py`

### compiled path / governance safety
- `pytest -q tests/test_default_runner_compiled_rule_path.py`

---

## 6) 진행 로그

### 2026-04-24

- merge 상태 재점검 후 `Now/Next/Later` 우선순위를 갱신했다.
- 반영한 완료 항목:
  - `PR-A1` internal import convergence 완료 (`scope_resolution_pass.py`, `inference_pass.py`, `semantic_pass.py`, `calculation_pass.py`)
  - `PR-A2` eager import guard 완료 (`comp.__init__` lazy export + `tests/test_package_smoke.py` 회귀 방지 테스트)
  - `PR-R2d` runtime/artifacts 이동 후 package 경로 import 정리 완료
- 다음 액션을 재정렬했다.
  1. `PR-R4` pass implementation relocation
  2. `PR-C1b` emit/governance boundary 코드 정리
  3. `PR-E` legacy top-level surface 축소

- 최근 merge 상태를 기준으로 체크리스트를 동기화했다.
- 반영한 완료 항목:
  - `lex_eval`, `source_eval`, `rule_eval` relocation 완료
  - `ast_nodes`, `spec_nodes`, `lex_ir`, `source_ir`, `rule_ir` relocation 완료
  - `compiled_spec` relocation 완료
  - `runtime_env` relocation 완료
  - `artifacts` relocation 완료
  - runner-adjacent relocation 완료
  - façade inventory / thinness audit 완료
  - façade thinness rule 문서화 완료
  - `comp.eval.compiled_expr` / `comp.eval.lex` / `comp.eval.source_module` / `comp.dsl.compiled_spec`의 package DSL import 정합성 확인
  - `AGENTS.md`에 병렬 작업용 `area:*` / `flow:*` label 축 추가
- 기존 `PR-R2: runtime/artifacts/compiled_spec`를 분리하고 마감 상태를 반영했다.
  - `compiled_spec`는 완료된 `PR-R2a`로 이동
  - `runtime_env`는 완료된 `PR-R2b`로 이동
  - `artifacts`는 완료된 `PR-R2c`로 이동
- `comp.pipeline_runner` / `comp.compiled_pipeline_runner`가 runner implementation을 소유하도록 이동했다.
- top-level runner files와 `comp.compat.*runner`는 package implementation wrapper로 축소했다.
- `docs/facade-inventory.md`를 추가해 wrapper / bridge / facade 상태를 분류했다.
- `docs/facade-thinness.md`를 추가해 wrapper 허용/금지 규칙을 정리했다.

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
