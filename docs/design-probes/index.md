# Design Probes

이 디렉토리는 아직 구현하지 않을 미래 아키텍처 방향을 안전하게 탐색하기 위한 공간이다.

중요:

```text
Design Probe는 implementation backlog가 아니다.
Design Probe는 현재 migration PR에 섞을 설계 변경도 아니다.
Design Probe는 반복해서 드러나는 설계 압력을 관찰하고, 승격/폐기 조건을 갖춘 가설로 보관하는 문서다.
```

---

## 목적

현재 migration issue는 의도적으로 실행 중심이다.

```text
implementation 이동
compatibility wrapper 유지
package / legacy parity 확인
behavior change 금지
```

이 방식은 안전하지만, 장기 설계 압력이 작업 중에 사라지거나 임시 대화에 묻힐 수 있다.

Design Probe lane은 그 중간층이다.

```text
미래 설계를 코드로 선점하지 않는다.
하지만 미래 설계 압력을 잊지도 않는다.
```

---

## 운영 모델

Design Probe는 bounded recursive design loop로 운영한다.

```text
Monitor
  PR / issue / test / docs 충돌 / 반복되는 코드 냄새를 관찰한다.

Analyze
  이 signal이 일회성 문제인지 구조 압력인지 판단한다.

Plan
  probe 갱신, architecture issue 후보, characterization test 후보를 만든다.

Execute
  기본적으로 docs / issue / test characterization까지만 허용한다.
  runtime behavior 변경은 별도 architecture/implementation issue 없이는 금지한다.

Knowledge
  docs/design-probes, migration-checklist, issue comments, PR notes를 공유 기억으로 둔다.
```

---

## 상태

각 probe는 다음 상태 중 하나를 가진다.

```text
watching
  관찰 중이지만 아직 강한 가설은 아니다.

active
  반복 signal이 있어 적극 추적한다.

promoted
  별도 architecture 또는 implementation issue로 승격되었다.

retired
  가설이 약해졌거나 더 작은 작업으로 해소되어 폐기되었다.

parked
  당장은 증거가 부족해 보류한다.
```

---

## 승격 원칙

Design Probe는 다음 조건 없이 구현 이슈로 승격하지 않는다.

```text
- hard trigger 또는 architectural trigger가 명시되어야 한다.
- 최소 2개 이상의 대안 또는 tradeoff가 비교되어야 한다.
- 구현하지 않을 범위가 명시되어야 한다.
- migration PR과 섞이지 않는 작은 implementation issue로 쪼갤 수 있어야 한다.
- disconfirming evidence를 검토해야 한다.
```

---

## 폐기 원칙

모든 probe가 구현으로 승격될 필요는 없다.

다음 경우 probe는 retired 될 수 있다.

```text
- migration 이후 문제가 더 이상 반복되지 않는다.
- current docs / compatibility policy만으로 충분히 설명 가능하다.
- candidate direction이 현재 model보다 명확한 이득을 만들지 못한다.
- 더 작은 test / docs / policy 작업으로 압력이 해소된다.
```

---

## 금지

Design Probe PR에서는 다음을 하지 않는다.

```text
- runtime refactor
- pass behavior change
- artifact schema change
- judgment core absorption
- public ledger implementation
- wrapper removal
- migration PR 안에 architecture refactor 섞기
```

---

## 작성법

새 probe는 `_template.md`를 복사해 작성한다.

최소한 다음을 포함해야 한다.

```text
Problem Pressure
Current Fact
Candidate Direction
MAPE-K Loop
Promotion Criteria
Retirement Criteria
Disconfirming Evidence
Guardrails
Probe Log
```

---

## Migration checklist와의 관계

활성 probe는 `docs/migration-checklist.md` 하단의 `Active Design Probes` 섹션에도 링크한다.

다만 그 섹션은 구현 대기열이 아니다.

```text
Migration checklist의 Now / Next / Later
  실제 실행 작업 큐

Active Design Probes
  미래 설계 압력 관찰판
```

---

## 초기 후보 예시

아래는 바로 구현할 작업이 아니라, 필요할 때 별도 issue로 열 수 있는 후보 예시다.

| Probe candidate | Pressure it would watch |
|---|---|
| StageState runtime direction | `CompileArtifacts` mutation 중심 흐름이 pass 간 상태 중복을 만들 때 |
| Projection-first public row model | row가 source-of-truth인지 projection인지 혼동이 반복될 때 |
| Receipt / ledger boundary | `merge_log`, `event_log`, `commit_log`, receipt, explanation view가 섞일 때 |
| Judgment runtime absorption | `RepairPass` / `GovernancePass` 책임 일부가 judgment core와 반복적으로 겹칠 때 |
| Scheduler / hazard scoreboard | full pass scan과 diagnostic/hazard state가 반복해서 비효율 또는 중복을 만들 때 |
