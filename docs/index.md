# docs

`comp` 내부 구조 문서 모음입니다.

이 디렉토리는 README보다 한 단계 깊은 **내부 지도**를 제공합니다.
목표는 모듈별 백과사전을 만드는 것이 아니라, 현재 구조와 장기 구조, 그리고 그 사이의 이행 상태를 명확히 드러내는 것입니다.

## 읽는 순서

### 처음 보는 경우
1. `../README.md`
2. `architecture.md`
3. `worked-example.md`
4. `current-pipeline.md`

### 현재 코드 흐름이 궁금한 경우
1. `current-pipeline.md`
2. `worked-example.md`
3. `migration-plan.md`
4. `migration-checklist.md`

### 새 설계 방향이 궁금한 경우
1. `architecture.md`
2. `worked-example.md`
3. `judgment-core.md`
4. `migration-plan.md`

### 판정 언어와 의미론이 궁금한 경우
1. `worked-example.md`
2. `judgment-language.md`
3. `core-semantics.md`
4. `judgment-core.md`

### spec 컴파일 경로가 궁금한 경우
1. `esgdl-reference.md`
2. `spec-pipeline.md`
3. `worked-example.md`

### 목표 실행 모델과 view 구조가 궁금한 경우
1. `worked-example.md`
2. `execution-model.md`
3. `views-ledger.md`
4. `migration-plan.md`

### 이행 작업을 issue로 나누고 싶은 경우
1. `migration-checklist.md`
2. `issue-plan.md`
3. `migration-plan.md`

## 문서 구성

- `architecture.md`
  - 레포 전체를 한 장으로 설명하는 중심 문서
  - 현재 구조 / 장기 구조 / bridge 상태를 함께 설명

- `current-pipeline.md`
  - 현재 staged pipeline의 실제 실행 흐름과 artifact 계약 설명

- `worked-example.md`
  - 작은 입력 하나를 현재 pipeline과 장기 judgment-first 관점으로 함께 따라가는 예제 문서

- `judgment-core.md`
  - 장기적으로 밀고 있는 judgment-first 구조와 현재 코드 연결점 설명

- `judgment-language.md`
  - data와 spec이 공유해야 할 공통 판정 어휘와 judgeable subject 설명

- `core-semantics.md`
  - 하나의 judgment core, fixpoint, frontier, commit shell 관점의 장기 의미론 설명

- `spec-pipeline.md`
  - ESGDL/spec가 parse → bind → lower → validate를 거쳐 실행 구조로 내려오는 경로 설명

- `execution-model.md`
  - staged pass를 장기적으로 어떤 runtime engine 경계로 재배치할지 설명

- `views-ledger.md`
  - 무엇이 authoritative state이고 무엇이 projection/view인지 설명

- `migration-plan.md`
  - 패키지화, façade 제거, judgment core 흡수 등 이행 작업 추적 문서

- `migration-checklist.md`
  - PR 단위 완료 조건과 현재 진행 상태를 추적하는 실행 체크리스트

- `issue-plan.md`
  - migration checklist를 실제 GitHub Issue 작업 단위로 내리는 운영 문서와 초기 issue 초안

- `testing.md`
  - 테스트가 무엇을 보호하는지 설명하는 문서

- `esgdl-reference.md`
  - ESGDL이 무엇을 선언하는 언어인지 설명하는 실용 참조 문서

## 문서 원칙

1. 현재 사실과 장기 방향을 섞어 쓰지 않는다.
2. 구현되지 않은 미래 구조를 이미 완료된 것처럼 쓰지 않는다.
3. bridge 상태를 숨기지 않는다.
4. README는 바깥 설명, `docs/`는 내부 지도로 역할을 분리한다.
5. judgment vocabulary와 formal semantics는 별도 문서에서 다루고, 현재 코드 흐름 문서와 섞지 않는다.
