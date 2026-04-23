# docs

`comp` 내부 구조 문서 모음입니다.

이 디렉토리는 README보다 한 단계 깊은 **내부 지도**를 제공합니다.
목표는 모듈별 백과사전을 만드는 것이 아니라, 현재 구조와 장기 구조, 그리고 그 사이의 이행 상태를 명확히 드러내는 것입니다.

## 읽는 순서

### 처음 보는 경우
1. `../README.md`
2. `architecture.md`
3. `current-pipeline.md`

### 현재 코드 흐름이 궁금한 경우
1. `current-pipeline.md`
2. `migration-plan.md`

### 새 설계 방향이 궁금한 경우
1. `architecture.md`
2. `judgment-core.md`
3. `migration-plan.md`

## 문서 구성

- `architecture.md`
  - 레포 전체를 한 장으로 설명하는 중심 문서
  - 현재 구조 / 장기 구조 / bridge 상태를 함께 설명

- `current-pipeline.md`
  - 현재 staged pipeline의 실제 실행 흐름과 artifact 계약 설명

- `judgment-core.md`
  - 장기적으로 밀고 있는 judgment-first 구조와 현재 코드 연결점 설명

- `migration-plan.md`
  - 패키지화, façade 제거, judgment core 흡수 등 이행 작업 추적 문서

- `testing.md`
  - 테스트가 무엇을 보호하는지 설명하는 문서

- `esgdl-reference.md`
  - ESGDL이 무엇을 선언하는 언어인지 설명하는 실용 참조 문서

## 문서 원칙

1. 현재 사실과 장기 방향을 섞어 쓰지 않는다.
2. 구현되지 않은 미래 구조를 이미 완료된 것처럼 쓰지 않는다.
3. bridge 상태를 숨기지 않는다.
4. README는 바깥 설명, `docs/`는 내부 지도로 역할을 분리한다.
