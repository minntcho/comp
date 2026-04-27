# Compatibility and Deprecation Policy

이 문서는 package-owned implementation으로 이동한 뒤에도 남아 있는 top-level wrapper와 compat wrapper를 어떻게 유지, 축소, 제거할지 정한다.

목표는 wrapper를 바로 제거하는 것이 아니다. 목표는 **무엇이 지원되는 compatibility path이고, 무엇이 임시 migration wrapper이며, 어떤 조건에서 제거 PR을 열 수 있는지**를 고정하는 것이다.

---

## 1. 현재 원칙

현재 `comp`는 implementation owner를 package path로 수렴시키고 있다.

```text
new code
  -> comp.* package path

legacy import path
  -> top-level compatibility wrapper

compat namespace
  -> compatibility wrapper or explicit bridge adapter
```

따라서 새 코드와 문서는 가능한 한 package path를 기준으로 써야 한다.

다만 top-level wrapper는 아직 제거하지 않는다. 기존 import 사용자, 테스트, 예제, downstream script가 깨질 수 있기 때문이다.

---

## 2. Wrapper categories

### 2.1 Supported compatibility path

기존 사용자를 깨지 않기 위해 당분간 명시적으로 지원하는 legacy path다.

예:

- `runtime_env.py` -> `comp.runtime_env`
- `artifacts.py` -> `comp.artifacts`
- `pipeline_runner.py` -> `comp.pipeline_runner`
- `compiled_pipeline_runner.py` -> `comp.compiled_pipeline_runner`
- `*_pass.py` -> `comp.pipeline.*`

정책:

- package implementation을 re-export한다.
- behavior를 추가하지 않는다.
- parity test로 object identity를 보호한다.
- 제거하려면 deprecation policy와 migration note가 먼저 필요하다.

---

### 2.2 Temporary migration wrapper

migration 중간 상태를 연결하기 위한 wrapper다.

현재 pass implementation relocation이 완료되면서 대부분의 temporary importlib bridge는 사라졌다. 앞으로 새 temporary wrapper가 생기면 반드시 later action을 기록한다.

정책:

- temporary임을 docs 또는 issue에 표시한다.
- 제거 또는 재분류 조건을 적는다.
- 장기 public API처럼 설명하지 않는다.

---

### 2.3 Public package facade

외부 사용자가 쓰기 좋은 package-level surface다.

예:

- `comp.runner`
- `comp.pipeline`
- `comp.eval`
- `comp.builtins`

정책:

- package 내부 구현 위치를 숨길 수 있다.
- public convenience를 제공할 수 있다.
- behavior semantics를 숨겨서 바꾸면 안 된다.

---

### 2.4 Explicit bridge adapter

단순 wrapper보다 두꺼운 번역 경계다.

예:

- `comp.compat.adapters`

정책:

- legacy shape와 target vocabulary 사이의 번역만 담당한다.
- unrelated behavior를 축적하지 않는다.
- judgment core가 더 많은 실행 경로를 직접 담당하게 되면 축소 후보가 된다.

---

## 3. Removal gates

wrapper 제거 PR은 아래 조건을 모두 만족해야 한다.

```text
[ ] package replacement path가 존재한다.
[ ] package path가 docs에서 primary path로 쓰인다.
[ ] parity test가 legacy path와 package path의 identity 또는 behavior equivalence를 보호한다.
[ ] 제거 대상이 supported compatibility path인지 temporary wrapper인지 분류되어 있다.
[ ] downstream compatibility risk가 PR 본문에 적혀 있다.
[ ] migration-checklist.md에 제거 단계가 반영되어 있다.
[ ] 제거가 behavior change와 섞이지 않는다.
```

하나라도 빠지면 wrapper 제거 PR을 열지 않는다.

---

## 4. Deprecation levels

### Level 0: Preserve

현재 기본값이다.

- wrapper를 유지한다.
- package implementation을 re-export한다.
- new code는 package path를 사용한다.
- tests는 parity를 보호한다.

### Level 1: Document package path as primary

- README / docs / examples에서 package path를 primary로 쓴다.
- legacy path는 compatibility path로만 언급한다.
- wrapper는 아직 유지한다.

### Level 2: Soft deprecation

- docs에서 legacy path를 deprecated 또는 legacy compatibility path로 표시한다.
- removal issue를 열 수 있다.
- 코드 warning은 선택 사항이다. warning 추가는 별도 PR로 다룬다.

### Level 3: Removal candidate

- parity tests와 migration notes가 준비되어 있다.
- downstream risk가 낮거나 명시적으로 수용된다.
- 제거 PR을 열 수 있다.

### Level 4: Removed

- wrapper가 제거된다.
- pyproject / packaging surface도 함께 정리한다.
- behavior change와 섞지 않는다.

---

## 5. Current policy table

| Surface | Current level | Primary path | Compatibility path | Notes |
|---|---:|---|---|---|
| Runtime environment | 0 | `comp.runtime_env` | `runtime_env.py` | Preserve until external usage risk is known |
| Artifacts | 0 | `comp.artifacts` | `artifacts.py` | Preserve until external usage risk is known |
| Runner | 0 | `comp.pipeline_runner`, `comp.runner` | `pipeline_runner.py` | Preserve; `comp.runner` remains public convenience facade |
| Compiled runner | 0 | `comp.compiled_pipeline_runner`, `comp.runner` | `compiled_pipeline_runner.py` | Preserve |
| Pipeline passes | 0 | `comp.pipeline.*` | `*_pass.py` | Preserve; all pass implementations are package-owned |
| Builtins | 0 | `comp.builtins.*` | old top-level builtin wrappers if present | Do not remove without inventory update |
| Eval / DSL / IR | 0 | `comp.eval.*`, `comp.dsl.*` | old top-level wrappers if present | Do not remove without inventory update |
| `comp.compat.adapters` | 0 | `comp.compat.adapters` | none | Bridge adapter, not a thin wrapper |

---

## 6. PR rules

### Compatibility-preserving wrapper PR

Allowed:

- re-export package implementation
- update `__all__`
- add parity tests
- update docs

Not allowed:

- behavior change
- semantic fallback
- pass order change
- architecture refactor

### Deprecation PR

Allowed:

- document primary package path
- mark legacy path as deprecated in docs
- add migration note
- optionally add warning, but only if explicitly scoped

Not allowed:

- wrapper removal
- behavior change
- broad import convergence unrelated to deprecation

### Removal PR

Allowed only after removal gates are satisfied.

Allowed:

- remove wrapper
- update packaging metadata
- update docs and tests

Not allowed:

- behavior change
- package relocation
- architecture refactor

---

## 7. Tests expected before removal

At minimum, wrapper removal planning should consider:

```bash
pytest -q tests/test_package_smoke.py
pytest -q tests/test_runner_package_facades.py tests/test_pipeline_package_facades.py
pytest -q tests/test_default_runner_compiled_rule_path.py
pytest -q
```

If a specific wrapper has dedicated package-location tests, include those too.

---

## 8. Current recommendation

For now, keep all top-level wrappers at **Level 0: Preserve**.

The next safe step is not removal. The next safe step is:

```text
Level 1: Document package path as primary
```

That means future PRs should gradually update docs, examples, and new code references to package paths while keeping legacy wrappers intact.
