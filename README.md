# comp

`comp`는 ESGDL 기반의 **실험적 evidence compiler**입니다.

이 레포는 raw fragment를 곧바로 “정답 표”로 바꾸는 도구라기보다, 후보·근거·충돌·정책을 축적한 뒤 **정당한 public row만 안전하게 승격**하는 구조를 목표로 합니다.

## 이 레포가 하려는 일

`comp`의 목표는 다음과 같습니다.

- ESG 관련 raw/반정형 입력에서 의미 있는 후보를 추출합니다.
- 후보 사이의 근거, 충돌, 보류 사유를 함께 보존합니다.
- 대표 후보를 고르고, 충분히 안전한 경우에만 public row를 만듭니다.
- provenance, hazard, governance를 잃지 않는 작은 compiler를 만듭니다.

즉 이 레포는 단순 parser나 ETL 스크립트가 아니라, **증거를 보존하면서 정제된 데이터를 public 상태로 승격하는 컴파일러**를 지향합니다.

## 현재 구현된 흐름

현재 레포는 stage pipeline 형태를 가지고 있습니다.

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

이 흐름에서 다음과 같은 중간 산출물을 다룹니다.

- fragments
- tokens
- claims
- frames
- rows
- calculations
- merge_log
- diagnostics

## 앞으로의 설계 방향

장기적으로 `comp`는 단순 pass chain을 넘어서, **같은 judgment language로 data와 spec을 함께 다루는 구조**를 목표로 합니다.

핵심 아이디어는 다음과 같습니다.

- raw 입력은 seed fact로 올립니다.
- DSL/spec는 monotone transfer rule로 컴파일합니다.
- core는 fixpoint engine 위에서 동작합니다.
- candidate selection은 frontier 계산으로 다룹니다.
- public row는 commit barrier를 통과한 projection만 허용합니다.
- provenance / hazard / receipt는 append-only 기록으로 남깁니다.

## 핵심 원칙

1. row-first가 아니라 judgment-first
2. append-only core
3. draft와 public row의 분리
4. emit은 source of truth가 아니라 projection
5. spec과 data를 같은 판정 어휘로 검증

## 패키지 구조

```text
comp/
  dsl/        # ESGDL grammar, DSL 관련 진입점
  judgment/   # future judgment core, fixpoint engine, frontier, commit
  pipeline/   # 현재 staged pass 공개 진입점
  eval/       # expression / rule / source evaluator 공개 진입점
  builtins/   # builtin 공개 진입점
  compat/     # 기존 artifacts/spec와의 bridge
  views/      # future draft/review/public projection
```

## 현재 상태

이 레포는 아직 **실험 단계**입니다.

- 구조 정리와 패키징이 진행 중입니다.
- API/CLI는 아직 안정화되지 않았습니다.
- 내부 파이프라인과 judgment core의 경계를 정리하는 중입니다.

즉 지금은 “완성된 제품”보다 **작은 evidence compiler의 올바른 구조를 찾는 단계**에 가깝습니다.

## 로드맵

### PR0
- 루트 `comp/` 패키지 도입
- `pyproject.toml` 추가
- 기존 top-level 모듈과의 호환 래퍼 추가
- 한글 README 추가

### PR1
- judgment core 뼈대 추가
- frontier / commit / receipts 자리 고정
- compat layer 정리

### PR2+
- 기존 pass를 judgment program 쪽으로 점진적으로 내리기
- emit/governance를 projection/commit 쪽으로 분리하기

## 지향점

`comp`는 결과 표만 맞는 시스템보다, **그 결과가 왜 정당한지까지 설명 가능한 시스템**을 지향합니다.

즉 이 레포의 목표는 단순 변환기가 아니라,

- 무엇이 후보인가
- 어떤 근거가 붙었는가
- 왜 이 값이 선택되었는가
- 왜 아직 public row가 되지 못하는가
- 어떤 조건에서 commit이 허용되는가

를 함께 다룰 수 있는 **작은 judgment machine**을 만드는 것입니다.
