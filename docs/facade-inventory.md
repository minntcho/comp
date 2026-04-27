# Facade Inventory

이 문서는 `comp` migration 중 남아 있는 package façade / compatibility wrapper / bridge adapter를 분류한다.

목표는 wrapper를 즉시 제거하는 것이 아니라, **어떤 파일이 공개 API 표면인지, 어떤 파일이 임시 bridge인지, 어떤 파일이 나중에 제거 후보인지**를 코드 기준으로 고정하는 것이다.

---

## 1. 분류 기준

### Actual implementation

실제 동작이나 데이터 구조를 소유하는 package module이다.

원칙:

- 새 코드가 우선 참조해야 하는 위치다.
- behavior는 이쪽에 있어야 한다.
- top-level legacy module이 남아 있더라도 implementation은 package 쪽이 source of truth다.

### Public API facade

외부 사용자가 쓰기 좋은 공개 import surface다.

원칙:

- 내부 구현 위치를 숨길 수 있다.
- 가벼운 기본값 주입이나 public constructor 제공은 가능하다.
- 의미 변경이나 stage behavior를 몰래 담으면 안 된다.

### Temporary migration bridge

아직 implementation이 legacy top-level에 남아 있어 package path에서 legacy object를 다시 내보내는 module이다.

원칙:

- migration 중 호환성을 위해 허용한다.
- 실제 behavior를 추가하지 않는다.
- 관련 implementation이 package로 이동하면 thin compatibility wrapper 또는 public facade로 재분류해야 한다.

### Legacy compatibility wrapper

기존 top-level import path를 깨지 않기 위해 남겨 둔 wrapper다.

원칙:

- package implementation을 re-export한다.
- 새 코드는 가능하면 package path를 쓴다.
- 충분한 deprecation / compatibility 방침이 생기기 전까지 제거하지 않는다.

### Bridge adapter

legacy artifact shape와 target judgment vocabulary 사이를 번역하는 module이다.

원칙:

- 단순 re-export보다 두꺼울 수 있다.
- 다만 임의 behavior 변경이 아니라 명시적 adapter 역할이어야 한다.
- 장기적으로 core 경계가 안정되면 축소 또는 재배치 후보가 된다.

---

## 2. 현재 inventory

### 2.1 Top-level package surface

| Module | Current role | Notes | Later action |
|---|---|---|---|
| `comp.__init__` | Public API facade | runner-facing symbols를 lazy export한다. | 유지하되 eager import는 계속 감시 |
| `comp.runner` | Public API facade | package runner implementation 위에 package-local default grammar path를 주입한다. | 유지 |
| `comp.pipeline_runner` | Actual implementation | staged runner implementation을 package가 소유한다. | 유지 |
| `comp.compiled_pipeline_runner` | Actual implementation | compiled runner implementation을 package가 소유한다. | 유지 |

`comp.runner`는 단순 re-export보다 조금 두껍다. 현재는 기본 grammar path를 package 내부로 잡아 주는 public convenience layer 역할을 한다. 실제 runner implementation은 `comp.pipeline_runner` / `comp.compiled_pipeline_runner`가 소유한다.

---

### 2.2 `comp.pipeline.*`

`comp.pipeline.__init__`은 current staged pipeline pass들을 공개하는 public pass facade다.

현재 하위 pass module은 package-owned implementation이다. Top-level pass files are now legacy compatibility wrappers that re-export these package implementations.

| Module | Current role | Legacy target | Later action |
|---|---|---|---|
| `comp.pipeline.lex` | Actual implementation | top-level `lex_pass.py` wrapper points here | 유지 |
| `comp.pipeline.parsing` | Actual implementation | top-level `parse_pass.py` wrapper points here | 유지 |
| `comp.pipeline.scope` | Actual implementation | top-level `scope_resolution_pass.py` wrapper points here | 유지 |
| `comp.pipeline.infer` | Actual implementation | top-level `inference_pass.py` wrapper points here | 유지 |
| `comp.pipeline.semantic` | Actual implementation | top-level `semantic_pass.py` wrapper points here | 유지 |
| `comp.pipeline.repair` | Actual implementation | top-level `repair_pass.py` wrapper points here | 유지 |
| `comp.pipeline.emit` | Actual implementation | top-level `emit_pass.py` wrapper points here | 유지 |
| `comp.pipeline.governance` | Actual implementation | top-level `governance_pass.py` wrapper points here | 유지 |
| `comp.pipeline.calculation` | Actual implementation | top-level `calculation_pass.py` wrapper points here | 유지 |

---

### 2.3 `comp.compat.*`

| Module | Current role | Notes | Later action |
|---|---|---|---|
| `comp.compat.pipeline_runner` | Legacy compatibility wrapper | `comp.pipeline_runner` package implementation을 re-export한다. | compatibility 방침 정리 후 제거/축소 검토 |
| `comp.compat.compiled_pipeline_runner` | Legacy compatibility wrapper | `comp.compiled_pipeline_runner` package implementation을 re-export한다. | compatibility 방침 정리 후 제거/축소 검토 |
| `comp.compat.artifacts` | Legacy compatibility wrapper | 이미 `comp.artifacts` package implementation을 re-export한다. | top-level compatibility 방침이 정리될 때까지 유지 |
| `comp.compat.adapters` | Bridge adapter | legacy artifact object를 judgment receipt / frontier / commit vocabulary로 번역한다. | judgment core absorption 이후 축소 또는 재배치 후보 |

`comp.compat.adapters`는 thin re-export가 아니다. 하지만 이 두꺼움은 현재 migration에서 허용되는 두꺼움이다. 이유는 이 module이 legacy staged pipeline과 judgment vocabulary 사이의 명시적 번역 경계이기 때문이다.

---

### 2.4 `comp.eval.*`

| Module | Current role | Notes | Later action |
|---|---|---|---|
| `comp.eval.__init__` | Public API facade | evaluator class들을 공개 surface로 묶는다. | 유지 |
| `comp.eval.expr` | Actual implementation | expression evaluator implementation을 package가 소유한다. | 유지 |
| `comp.eval.compiled_expr` | Actual implementation | compiled/rule expression bridge evaluator를 package가 소유한다. | 유지 |
| `comp.eval.lex` | Actual implementation | lex expression evaluator를 package가 소유한다. | 유지 |
| `comp.eval.source_module` | Actual implementation | source expression evaluator를 package가 소유한다. | 유지 |
| `comp.eval.rule` | Actual implementation | rule evaluator implementation을 package가 소유한다. | 유지 |

`comp.eval.*`은 이미 relocation이 상당히 진행된 영역이다. 새 code는 이 package path를 기준으로 쓰는 것이 맞다.

---

### 2.5 `comp.builtins.*`

| Module | Current role | Notes | Later action |
|---|---|---|---|
| `comp.builtins.__init__` | Public API facade | default builtin registration helpers를 공개한다. | 유지 |
| `comp.builtins.esg` | Actual implementation | ESG builtin functions와 default registration을 소유한다. | 유지 |
| `comp.builtins.rule` | Actual implementation | rule builtin registry와 builtin spec을 소유한다. | 유지 |

`comp.builtins.*` 역시 package-owned implementation 쪽으로 정리된 영역이다.

---

### 2.6 Relocated top-level compatibility wrappers

| Module | Current role | Package target | Later action |
|---|---|---|---|
| `runtime_env.py` | Legacy compatibility wrapper | `comp.runtime_env` | compatibility policy 이후 제거/축소 검토 |
| `artifacts.py` | Legacy compatibility wrapper | `comp.artifacts` | compatibility policy 이후 제거/축소 검토 |
| `pipeline_runner.py` | Legacy compatibility wrapper | `comp.pipeline_runner` | compatibility policy 이후 제거/축소 검토 |
| `compiled_pipeline_runner.py` | Legacy compatibility wrapper | `comp.compiled_pipeline_runner` | compatibility policy 이후 제거/축소 검토 |
| `lex_pass.py` | Legacy compatibility wrapper | `comp.pipeline.lex` | compatibility policy 이후 제거/축소 검토 |
| `parse_pass.py` | Legacy compatibility wrapper | `comp.pipeline.parsing` | compatibility policy 이후 제거/축소 검토 |
| `scope_resolution_pass.py` | Legacy compatibility wrapper | `comp.pipeline.scope` | compatibility policy 이후 제거/축소 검토 |
| `inference_pass.py` | Legacy compatibility wrapper | `comp.pipeline.infer` | compatibility policy 이후 제거/축소 검토 |
| `semantic_pass.py` | Legacy compatibility wrapper | `comp.pipeline.semantic` | compatibility policy 이후 제거/축소 검토 |
| `repair_pass.py` | Legacy compatibility wrapper | `comp.pipeline.repair` | compatibility policy 이후 제거/축소 검토 |
| `emit_pass.py` | Legacy compatibility wrapper | `comp.pipeline.emit` | compatibility policy 이후 제거/축소 검토 |
| `governance_pass.py` | Legacy compatibility wrapper | `comp.pipeline.governance` | compatibility policy 이후 제거/축소 검토 |
| `calculation_pass.py` | Legacy compatibility wrapper | `comp.pipeline.calculation` | compatibility policy 이후 제거/축소 검토 |

이 파일들은 더 이상 top-level implementation으로 보면 안 된다. 현재는 legacy import path 보존을 위한 wrapper다.

---

### 2.7 Remaining top-level implementations

No staged pipeline pass implementations remain top-level-owned. The remaining top-level files are compatibility wrappers or non-pass legacy surfaces.

---

## 3. Removal candidates

즉시 제거하지 않는다. 제거 후보는 다음 조건이 충족된 뒤에만 다룬다.

| Candidate | Remove only after |
|---|---|
| `comp.compat.pipeline_runner` / `compiled_pipeline_runner` wrappers | compatibility / deprecation policy가 정리된 뒤 |
| top-level `runtime_env.py` / `artifacts.py` wrappers | compatibility / deprecation policy가 정리된 뒤 |
| top-level `pipeline_runner.py` / `compiled_pipeline_runner.py` wrappers | compatibility / deprecation policy가 정리된 뒤 |
| top-level pass wrappers (`*_pass.py`) | compatibility / deprecation policy가 정리된 뒤 |
| old top-level evaluator / DSL / IR wrappers | package path가 충분히 안정되고 downstream compatibility 방침이 정리된 뒤 |
| `comp.compat.adapters` | judgment core가 더 많은 실행 경로를 직접 담당하고 legacy artifact translation 경계가 줄어든 뒤 |

---

## 4. Current risks

### 4.1 Eager import risk

`comp.__init__` lazily resolves runner-facing symbols so plain `import comp` should not eagerly import runner implementation.

This should continue to be audited under A-track eager import / cycle work.

### 4.2 Compatibility surface drift risk

Pipeline pass implementations are package-owned, while top-level compatibility wrappers still remain. Future PRs should keep wrapper identity parity until a compatibility / deprecation policy is written.

### 4.3 Adapter thickness risk

`comp.compat.adapters` contains real translation logic. That is acceptable because it is an explicit bridge adapter, not a hidden wrapper. Future PRs should avoid adding unrelated behavior there.

---

## 5. Guidance for future PRs

1. Do not remove wrappers in inventory-only PRs.
2. Do not mix facade removal with behavior changes.
3. Do not describe a package facade as package-owned implementation unless the implementation actually lives there.
4. Keep temporary bridge wrappers thin.
5. Put behavior in package-owned implementation modules, not in legacy compatibility wrappers.
6. When a bridge must be thick, name it as an adapter and explain what boundary it translates.

---

## 6. Follow-up

The natural follow-up is compatibility / deprecation policy for top-level wrappers.

That follow-up should define:

- which legacy wrappers remain supported import paths
- which wrappers are temporary migration artifacts
- when wrapper removal is allowed
- what parity tests must exist before removal
