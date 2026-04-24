# Facade Thinness Rules

이 문서는 `comp` migration 중 façade / wrapper / bridge module이 얼마나 얇아야 하는지 정한다.

`docs/facade-inventory.md`가 현재 wrapper들을 분류하는 문서라면, 이 문서는 이후 PR에서 wrapper를 어떻게 다뤄야 하는지 정하는 규칙이다.

목표는 간단하다.

> wrapper는 경로 호환성과 공개 표면을 위해 존재한다.  
> behavior는 가능한 한 package-owned implementation에 있어야 한다.

---

## 1. 기본 원칙

### Rule 1. Wrapper must not hide behavior

wrapper는 의미 변경을 숨기면 안 된다.

허용:

- re-export
- `__all__` 정리
- import path compatibility 유지
- public convenience 기본값 주입
- explicit adapter boundary에서의 번역

금지:

- pipeline stage의 의미 변경
- selection / commit / governance 판단 변경
- diagnostic / error / warning 생성 규칙 변경
- row materialization 방식 변경
- calculation 결과 변경
- import side effect에 의존하는 behavior 추가

즉 wrapper가 들어간 PR에서 결과 artifact가 달라진다면 그 PR은 thin wrapper PR이 아니다.

---

### Rule 2. Implementation ownership must be visible

실제 구현 소유자는 명확해야 한다.

원칙:

```text
actual behavior
  -> package-owned implementation

legacy import path
  -> compatibility wrapper

package public convenience path
  -> public API facade

legacy shape ↔ target vocabulary
  -> explicit bridge adapter
```

문서나 PR 본문에서 package module을 implementation이라고 부르려면, 실제 구현이 그 package path 안에 있어야 한다.

`comp.pipeline.emit`처럼 package path가 있어도 top-level `emit_pass`를 importlib로 다시 내보내는 경우에는 **package-owned implementation**이라고 부르면 안 된다.

---

### Rule 3. Do not mix wrapper work with behavior work

다음 작업은 같은 PR에 섞지 않는다.

```text
- wrapper inventory
- wrapper thinness cleanup
- actual relocation
- import convergence
- behavior change
- architecture refactor
- facade removal
```

예외가 필요하면 PR 본문에 이유를 명시한다.

---

## 2. Allowed patterns

### 2.1 Pure re-export wrapper

가장 얇은 wrapper다.

예:

```python
from comp.artifacts import CompileArtifacts, ClaimArtifact

__all__ = ["CompileArtifacts", "ClaimArtifact"]
```

허용 조건:

- package implementation을 그대로 내보낸다.
- 객체 identity가 보존된다.
- 새 behavior를 추가하지 않는다.

적합한 위치:

- top-level legacy compatibility wrapper
- package compatibility wrapper

---

### 2.2 Importlib legacy bridge

아직 implementation이 top-level legacy module에 남아 있을 때 임시로 허용되는 bridge다.

예:

```python
import importlib

_legacy = importlib.import_module("emit_pass")
EmitPass = getattr(_legacy, "EmitPass")

__all__ = ["EmitPass"]
```

허용 조건:

- migration 중임이 문서에 명시되어 있다.
- 새 behavior를 추가하지 않는다.
- later action이 inventory에 기록되어 있다.

주의:

- 이 패턴은 완료 상태가 아니다.
- actual relocation이 끝나면 package implementation re-export 또는 public facade로 재분류해야 한다.

---

### 2.3 Public convenience facade

외부 사용자가 쓰기 좋은 공개 표면을 만들기 위해 아주 얇은 편의 계층은 허용된다.

예:

- package-local default grammar path 주입
- public runner class 이름 제공
- 안정적인 `__all__` export 제공

허용 조건:

- convenience가 behavior semantics를 바꾸지 않는다.
- 내부 implementation owner가 명확하다.
- default가 바뀌면 테스트나 PR 본문에서 명시한다.

`comp.runner`는 이 범주에 해당한다. 기본 grammar path를 package 내부로 잡아 주는 public convenience layer이고, 실제 runner behavior는 `comp.pipeline_runner` / `comp.compiled_pipeline_runner`가 소유한다.

---

### 2.4 Explicit bridge adapter

단순 wrapper보다 두꺼운 module이 필요한 경우가 있다.

예:

- legacy artifact object를 judgment receipt로 번역
- legacy row snapshot을 commit barrier vocabulary로 번역
- staged pipeline artifact와 target semantics 사이의 명시적 adapter

허용 조건:

- 파일 이름이나 문서에서 adapter임이 드러난다.
- 어떤 두 경계를 번역하는지 설명되어 있다.
- 무관한 behavior를 추가하지 않는다.
- 장기 축소 또는 재배치 후보로 기록한다.

`comp.compat.adapters`는 이 예외에 해당한다.

---

## 3. Disallowed patterns

### 3.1 Behavior-bearing compatibility wrapper

금지 예:

```python
from comp.artifacts import CompileArtifacts

class CompileArtifacts(CompileArtifacts):
    def add_claim(self, claim):
        # compatibility wrapper에서 새 semantics 추가
        ...
```

이런 변경은 wrapper가 아니라 behavior change다.

---

### 3.2 Hidden architecture migration

금지 예:

- `comp.pipeline.emit` wrapper 안에서 public projection semantics를 새로 구현
- `comp.pipeline.governance` wrapper 안에서 commit barrier 판단을 바꿈
- compatibility wrapper에서 pass order를 바꿈

architecture work는 별도 issue / PR로 분리한다.

---

### 3.3 Import cleanup disguised as facade cleanup

wrapper cleanup PR에서 광범위한 import convergence를 같이 하면 안 된다.

예:

- `comp.pipeline.*` wrapper 정리하면서 동시에 runner-adjacent imports 전체를 바꿈
- facade inventory 문서 PR에서 implementation import path를 대량 변경

import convergence는 A-track에서 다룬다.

---

### 3.4 Removal without parity

wrapper 제거는 다음이 없으면 금지한다.

- replacement package path
- compatibility / deprecation 방침
- smoke or parity test
- migration checklist update

---

## 4. Classification-specific rules

### 4.1 Public API facade

허용:

- stable import name 제공
- public constructor 제공
- minimal default value 주입
- package-local resource path 연결

금지:

- internal stage semantics 변경
- hidden fallback behavior 추가
- broad import-time side effects

검증:

- package smoke test
- public import path test

---

### 4.2 Temporary migration bridge

허용:

- legacy implementation import
- object re-export
- `__all__` 정리

금지:

- behavior 추가
- partial reimplementation
- silent fallback
- extra policy / diagnostic / validation logic

검증:

- package import와 legacy import가 같은 객체를 가리키는지 확인
- relocation 이후 재분류 필요

---

### 4.3 Legacy compatibility wrapper

허용:

- package implementation re-export
- legacy path 유지
- identity parity 유지

금지:

- package implementation과 다른 subclass / proxy 생성
- compatibility path만의 behavior 추가
- deprecation 없이 제거

검증:

- legacy import와 package import identity test

---

### 4.4 Bridge adapter

허용:

- explicit translation
- target vocabulary projection
- legacy shape normalization

금지:

- unrelated behavior accumulation
- architecture decision을 adapter 안에 숨김
- permanent catch-all utility module화

검증:

- adapter input/output contract test
- docs에서 번역 경계 설명

---

## 5. PR checklist for wrapper changes

Wrapper / facade 관련 PR은 다음을 확인한다.

```text
[ ] 이 PR은 wrapper/facade 작업인가, relocation인가, behavior change인가?
[ ] implementation owner가 명확한가?
[ ] wrapper에 새 semantics가 들어가지 않았는가?
[ ] legacy path와 package path의 object identity가 필요한 경우 보존되는가?
[ ] temporary bridge라면 later action이 기록되어 있는가?
[ ] 제거 후보라면 제거 조건이 충족되었는가?
[ ] migration-checklist.md 갱신이 필요한가?
```

---

## 6. Current application to this repo

현재 inventory 기준으로 적용하면 다음과 같다.

- `comp.eval.*`, `comp.builtins.*`, `comp.pipeline_runner`, and `comp.compiled_pipeline_runner`
  - package-owned implementation 영역이다.
  - 새 code는 이 경로를 기준으로 써야 한다.

- `runtime_env.py`, `artifacts.py`, `pipeline_runner.py`, and `compiled_pipeline_runner.py`
  - legacy compatibility wrapper다.
  - package implementation을 re-export해야 하며 behavior를 추가하면 안 된다.

- `comp.pipeline.*`
  - 대부분 temporary migration bridge다.
  - pass implementation relocation 전까지는 제거하지 않는다.
  - package-owned implementation처럼 설명하면 안 된다.

- `comp.compat.pipeline_runner` and `comp.compat.compiled_pipeline_runner`
  - legacy compatibility wrapper다.
  - package runner implementation을 re-export해야 하며 runner behavior를 추가하면 안 된다.

- `comp.runner`
  - public convenience facade다.
  - package-owned runner implementation 위에 default grammar path를 주입한다.

- `comp.compat.adapters`
  - explicit bridge adapter다.
  - 단순 re-export보다 두꺼울 수 있지만, legacy artifact와 judgment vocabulary 사이의 번역 경계에 머물러야 한다.

---

## 7. Follow-up work

이 규칙은 wrapper를 즉시 제거하지 않는다.

다음 follow-up은 별도 issue / PR로 나눈다.

- eager import / cycle audit
- pass implementation relocation
- compatibility wrapper deprecation policy
- adapter boundary tests
- actual wrapper removal
