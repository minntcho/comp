# Design Probe: <name>

## Status

```text
watching | active | promoted | retired | parked
```

Current status: `watching`

---

## Problem Pressure

현재 migration / architecture 작업에서 반복해서 드러나는 압력을 적는다.

예:

```text
- 같은 책임이 여러 pass에 반복된다.
- current fact와 target semantics를 문서에서 계속 분리하기 어렵다.
- wrapper / facade / adapter 경계가 반복해서 흐려진다.
- row / receipt / log / ledger 의미가 PR마다 다시 충돌한다.
```

---

## Current Fact

현재 코드는 실제로 무엇을 하는가?

주의:

```text
현재 구현 사실과 미래 candidate direction을 섞지 않는다.
구현되지 않은 target semantics를 이미 완료된 것처럼 쓰지 않는다.
```

---

## Candidate Direction

미래에 고려할 수 있는 방향을 적는다.

주의:

```text
확정 표현을 피한다.
이 방향으로 간다는 선언이 아니라, 검토할 후보로 적는다.
```

---

## MAPE-K Loop

### Monitor

어떤 signal을 관찰할 것인가?

예:

```text
- 관련 PR에서 반복되는 책임 경계 혼동
- 같은 종류의 test fixture 중복
- 같은 bug / regression 재발
- docs에서 current fact와 target semantics 충돌
```

### Analyze

signal을 어떤 기준으로 구조 압력이라고 판단할 것인가?

예:

```text
- 1회성 작업 실수가 아니라 2회 이상 반복되는가?
- 같은 책임이 3개 이상 파일에 분산되는가?
- migration PR에서 architecture 설명이 계속 필요해지는가?
```

### Plan

이 probe가 어떤 후속 행동으로 이어질 수 있는가?

예:

```text
- characterization test 추가
- docs boundary 정리
- architecture issue 생성
- implementation issue 후보 분할
```

### Execute

지금 허용되는 실행 범위를 적는다.

기본값:

```text
- docs 갱신 허용
- issue comment 허용
- characterization test 후보 제안 허용
- runtime behavior 변경 금지
- schema 변경 금지
- relocation PR과 혼합 금지
```

### Knowledge

관련 문서, issue, PR, tests를 적는다.

---

## Promotion Criteria

이 probe를 architecture issue 또는 implementation issue로 승격할 조건을 적는다.

### Hard Triggers

가능하면 수치화한다.

예:

```text
- 같은 책임 중복이 3개 이상 파일에서 발견된다.
- 같은 boundary bug가 2회 이상 발생한다.
- 같은 종류의 test fixture 중복이 3회 이상 반복된다.
- 측정 가능한 성능 저하 또는 pass 비용 증가가 관찰된다.
```

### Architectural Triggers

수치화하기 어렵지만 반복되는 구조 압력을 적는다.

예:

```text
- 현재 구조로는 책임 경계를 설명하기 어려운 PR이 반복된다.
- current fact와 target semantics를 계속 분리하기 어려워진다.
- compatibility wrapper가 사실상 behavior를 품기 시작한다.
- row / receipt / log / ledger 의미가 코드에서 반복적으로 충돌한다.
```

### Required Before Promotion

승격 전 필수 조건을 적는다.

```text
- 최소 2개 이상의 대안을 비교한다.
- 구현하지 않을 범위를 명시한다.
- migration PR과 섞이지 않는 작은 implementation issue로 쪼갤 수 있어야 한다.
- disconfirming evidence를 검토한다.
```

---

## Retirement Criteria

이 probe를 폐기할 조건을 적는다.

예:

```text
- 관련 migration 이후 문제가 반복되지 않는다.
- current docs / compatibility policy만으로 충분히 설명 가능하다.
- candidate direction이 현재 model보다 명확한 이득을 만들지 못한다.
- 더 작은 docs / test / policy 작업으로 압력이 해소된다.
```

---

## Disconfirming Evidence

이 probe가 틀렸거나 약하다고 볼 수 있는 증거를 적는다.

예:

```text
- migration이 끝난 뒤 문제 signal이 사라진다.
- 현재 artifact model이 더 단순하고 충분하다.
- proposed direction이 testability를 낮춘다.
- proposed direction이 compatibility cost를 과도하게 키운다.
```

---

## Guardrails

이 probe가 현재 migration 작업을 오염시키지 않도록 막는 규칙을 적는다.

기본값:

```text
- 이 probe는 exploration-only다.
- 이 probe만으로 runtime behavior를 바꾸지 않는다.
- implementation은 별도 architecture / implementation issue가 필요하다.
- migration PR 안에 이 probe의 target design을 끼워 넣지 않는다.
- 현재 구현 사실을 target semantics처럼 문서화하지 않는다.
```

---

## Related Migration Work

관련 migration issue / PR / docs를 적는다.

---

## Probe Log

### YYYY-MM-DD

```text
Observation:
Hypothesis:
Decision:
Next watch:
```
