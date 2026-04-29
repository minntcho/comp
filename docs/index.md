# docs

`comp` 내부 구조 문서 모음입니다.

이 디렉토리는 README보다 한 단계 깊은 **내부 지도**를 제공합니다.
다만 앞으로의 rebuild / architecture correction 작업은 먼저 active authority docs를 기준으로 판단합니다.

---

## Active architecture policy

현재 active policy는 다음 문서를 우선합니다.

1. `architecture/authority-map.md`
2. `architecture/kill-list.md`

이 두 문서는 파일 이동보다 먼저 다음 질문을 고정합니다.

```text
무엇이 source of truth인가?
무엇이 derived projection인가?
무엇이 legacy transport인가?
무엇을 장기 구조에서 죽여야 하는가?
```

앞으로 relocation / wrapper / facade / pipeline 작업은 이 두 문서를 통과해야 합니다.

---

## Archived migration state

이전 package migration / facade / compatibility 흐름은 보존하되 active architecture policy로 쓰지 않습니다.

- 현재 main 기준 migration state 보존 branch:
  - `legacy/current-migration-state-20260429`
- archive 안내:
  - `archive/2026-migration/README.md`

Archive 문서는 증거물과 참고자료입니다. 새 구현 지침으로 직접 사용하지 않습니다.

---

## 읽는 순서

### 새 구조를 다시 잡는 경우
1. `architecture/authority-map.md`
2. `architecture/kill-list.md`
3. `judgment-core.md`
4. `emit-governance-boundary.md`
5. `views-ledger.md`

### 현재 코드 흐름이 궁금한 경우
1. `current-pipeline.md`
2. `emit-governance-boundary.md`
3. `worked-example.md`

### 판정 언어와 의미론이 궁금한 경우
1. `worked-example.md`
2. `judgment-language.md`
3. `core-semantics.md`
4. `judgment-core.md`

### spec 컴파일 경로가 궁금한 경우
1. `esgdl-reference.md`
2. `spec-pipeline.md`
3. `worked-example.md`

### 과거 migration / compatibility 상태를 확인하는 경우
1. `archive/2026-migration/README.md`
2. `migration-checklist.md`
3. `migration-plan.md`
4. `facade-inventory.md`
5. `facade-thinness.md`
6. `compatibility-policy.md`

주의: 위 migration / compatibility 문서는 historical reference입니다. active architecture policy로 쓰지 않습니다.

---

## 문서 구성

### Active policy

- `architecture/authority-map.md`
  - source of truth, derived projection, legacy transport, layer별 권한을 고정하는 active policy

- `architecture/kill-list.md`
  - 장기 구조에서 authoritative state로 살아남으면 안 되는 개념을 고정하는 문서

### Core explanation

- `architecture.md`
  - 레포 전체를 한 장으로 설명하는 중심 문서
  - 현재 구조 / 장기 구조 / bridge 상태를 함께 설명

- `current-pipeline.md`
  - 현재 staged pipeline의 실제 실행 흐름과 artifact 계약 설명

- `emit-governance-boundary.md`
  - `EmitPass`를 projection boundary로, `GovernancePass`를 barrier / decision / receipt-adjacent boundary로 분리해서 설명하는 문서

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

### Historical / migration references

- `migration-plan.md`
  - 패키지화, façade 제거, judgment core 흡수 등 과거 이행 작업 추적 문서

- `migration-checklist.md`
  - PR 단위 완료 조건과 진행 상태를 추적하던 실행 체크리스트

- `issue-plan.md`
  - migration checklist를 실제 GitHub Issue 작업 단위로 내리는 운영 문서와 초기 issue 초안

- `facade-inventory.md`
  - package façade / compatibility wrapper / temporary bridge 상태를 분류하는 inventory 문서

- `facade-thinness.md`
  - façade / wrapper / bridge가 허용하는 얇은 역할과 금지되는 behavior를 정리하는 규칙 문서

- `compatibility-policy.md`
  - top-level wrapper / compat wrapper의 유지, deprecation, removal gate를 정리하는 정책 문서

- `archive/2026-migration/README.md`
  - 이전 migration state를 active policy와 분리하기 위한 archive 안내 문서

### Exploration

- `design-probes/index.md`
  - 미래 아키텍처 방향을 구현 대기열이 아니라 관찰 가능한 설계 가설로 관리하는 운영 문서

- `design-probes/_template.md`
  - Design Probe 작성 템플릿. promotion / retirement criteria, disconfirming evidence, guardrail을 포함한다.

### Other references

- `testing.md`
  - 테스트가 무엇을 보호하는지 설명하는 문서

- `esgdl-reference.md`
  - ESGDL이 무엇을 선언하는 언어인지 설명하는 실용 참조 문서

---

## 문서 원칙

1. active policy와 historical reference를 섞지 않는다.
2. 현재 사실과 장기 방향을 섞어 쓰지 않는다.
3. 구현되지 않은 미래 구조를 이미 완료된 것처럼 쓰지 않는다.
4. bridge 상태를 숨기지 않되, bridge를 active target으로 승격하지 않는다.
5. README는 바깥 설명, `docs/`는 내부 지도로 역할을 분리한다.
6. judgment vocabulary와 formal semantics는 별도 문서에서 다루고, 현재 코드 흐름 문서와 섞지 않는다.
7. Design Probe는 구현 대기열이 아니라 미래 설계 압력 관찰판으로 유지한다.
8. relocation 작업은 active authority docs를 먼저 통과해야 한다.
