# LLM-Orchestrated Compiler Tool Loop

이 문서는 `comp`의 장기 방향 중 하나인 **LLM 주도 해석 루프와 compiler tool 검증 구조**를 계획 수준에서 고정한다.

핵심 아이디어는 컴파일러가 전체 루프를 직접 주도하는 것이 아니라, **LLM agent가 컴파일러를 하나의 tool로 반복 호출하면서 해석을 안정화한다**는 점이다.

```text
LLM proposes interpretations.
Compiler returns obligations.
LLM resolves obligations.
Receipt records the stabilized result.
```

한국어로 줄이면 다음과 같다.

```text
LLM이 해석을 만들고,
컴파일러가 그 해석이 아직 무엇을 증명해야 하는지 알려주고,
LLM이 그 의무사항을 해결하고,
receipt가 공개 가능한 경계를 확정한다.
```

---

## 1. 배경

기존의 정적 컴파일러 중심 설계는 명시된 규칙을 안정적으로 검사할 수 있다. 하지만 컴파일러는 지능이 없기 때문에 **정의되지 않은 의미 영역**을 스스로 발견하지 못한다.

예를 들어 컴파일러가 다음 규칙만 알고 있다면:

```text
amount는 숫자여야 한다.
unit은 허용 목록에 있어야 한다.
public value는 source witness를 가져야 한다.
```

다음과 같은 의미 영역은 조용히 빠질 수 있다.

```text
factor version과 period의 호환성
market-based / location-based electricity 구분
중복 invoice line 처리
month-only period에 필요한 reporting year context
source header가 row cell에 부여하는 implicit unit
```

따라서 단순히 고정된 컴파일러를 강화하는 것만으로는 부족하다.

새 방향은 다음과 같다.

```text
LLM이 넓게 해석한다.
Compiler tool이 그 해석을 기계적으로 검사한다.
Compiler tool은 실패, 미지, 미검사 영역, proof obligation을 구조화해서 반환한다.
LLM은 그 diagnostic을 읽고 evidence/rule/context를 더 찾아 해석을 수정한다.
이 루프를 receipt-ready 상태까지 반복한다.
```

---

## 2. 핵심 원칙

### 2.1 LLM은 해석자다

LLM은 raw evidence, compiler diagnostic, rule gaps, semantic issues를 보고 다음 해석 후보를 만든다.

LLM이 할 수 있는 일:

```text
candidate interpretation 제안
missing evidence 탐색
unchecked area 해석
rule template 후보 제안
canonical sentence 검토
review question 생성
```

### 2.2 Compiler는 obligation oracle이다

컴파일러는 지능형 판단자가 아니라, LLM이 만든 해석을 명시적 계약에 대고 검사하는 tool이다.

Compiler tool이 해야 하는 일:

```text
source witness 검사
type/unit 검사
compatibility 검사
conflict 검사
rule coverage 검사
receipt precondition 검사
proof obligation 산출
```

### 2.3 Receipt는 public truth boundary다

LLM이 루프를 주도하더라도 public output의 권위는 LLM에게 있지 않다.

```text
해석 탐색 authority = LLM
검증 authority = compiler report
공개 authority = governance / receipt
```

LLM이 “맞다”고 말해도 compiler가 receipt-ready 상태를 주지 않으면 public projection은 생성되지 않는다.

---

## 3. 전체 흐름

```text
Raw Evidence
  ↓
LLM Agent
  - initial interpretation
  - source/context search
  - rule gap reasoning
  ↓ hypothesis
Compiler Tool
  - deterministic validation
  - diagnostics
  - obligations
  ↓ compile report
LLM Agent
  - revise interpretation
  - resolve obligations
  - propose rule/template if needed
  ↓ repeated hypothesis
Compiler Tool
  ↓ accepted / review_required / blocked
Governance
  ↓ decision
Receipt Ledger
  ↓
Public Projection
```

더 짧게 표현하면:

```text
Hypothesis → Compile → Diagnose → Revise → Compile → ... → Receipt
```

---

## 4. Compiler tool의 반환 상태

이 구조에서는 pass/fail만으로 부족하다. 최소 네 가지 상태가 필요하다.

```text
pass
fail
unknown
unchecked
```

### pass

명시적 evidence와 rule로 통과한 상태.

```text
amount=1200 has source span S1.
unit=kWh is allowed for electricity.
```

### fail

명시적 룰 위반이 있는 상태.

```text
unit=kWh was claimed, but no source witness exists.
```

### unknown

추가 context가 없어서 판정할 수 없는 상태.

```text
period=Jan exists, but reporting year is missing.
```

### unchecked

현재 컴파일러가 검사할 rule family 자체를 갖고 있지 않은 상태.

```text
factor_period_compatibility has no active rule.
```

`unchecked`는 이 설계에서 매우 중요하다. 기존 고정 컴파일러의 가장 위험한 실패는 “검사할 룰이 없어서 조용히 통과하는 것”이다. 이 문서의 구조에서는 그런 경우를 통과가 아니라 `unchecked` 또는 `missing_rule_coverage`로 보고해야 한다.

---

## 5. CompileReport 계약

Compiler tool은 단순 boolean을 반환하면 안 된다. LLM이 다음 행동을 결정할 수 있는 구조화된 report를 반환해야 한다.

예상 형태:

```python
@dataclass(frozen=True)
class CompileReport:
    status: Literal[
        "accepted",
        "blocked",
        "review_required",
        "underconstrained",
        "unchecked",
    ]
    passed_claims: tuple[CheckedClaim, ...]
    failed_claims: tuple[FailedClaim, ...]
    unknowns: tuple[UnknownClaim, ...]
    unchecked_areas: tuple[UncheckedArea, ...]
    obligations: tuple[ProofObligation, ...]
    hazards: tuple[Hazard, ...]
    receipt_preconditions: tuple[ReceiptPrecondition, ...]
```

예시 report:

```json
{
  "status": "blocked",
  "passed_claims": [
    {
      "field": "activity",
      "value": "electricity",
      "witness": "span_1"
    },
    {
      "field": "amount",
      "value": 1200,
      "witness": "span_2"
    }
  ],
  "failed_claims": [
    {
      "field": "unit",
      "value": "kWh",
      "reason": "missing_source_witness",
      "origin": "llm_inferred"
    }
  ],
  "unknowns": [
    {
      "field": "period.year",
      "reason": "context_required"
    }
  ],
  "obligations": [
    {
      "kind": "find_source_witness",
      "field": "unit"
    },
    {
      "kind": "find_context",
      "field": "reporting_year"
    }
  ],
  "can_project_public_row": false
}
```

---

## 6. Proof obligation

이 설계에서 compiler diagnostic은 단순 에러 메시지가 아니다. LLM이 다음에 해결해야 하는 **채무 목록**이다.

대표 obligation:

```text
find_source_witness
find_context
resolve_conflict
instantiate_rule
request_human_review
mark_missing_evidence
lower_claim_strength
```

예시:

```json
{
  "kind": "find_source_witness",
  "field": "unit",
  "acceptable_sources": [
    "same_fragment",
    "nearby_header",
    "table_column_unit"
  ]
}
```

LLM은 이 obligation을 보고 다음 행동을 결정한다.

```text
unit source를 같은 fragment에서 찾는다.
없으면 table header에서 찾는다.
그래도 없으면 unit을 확정하지 않고 missing_unit hazard로 낮춘다.
```

---

## 7. 예시 루프

입력:

```text
전력 사용량 1,200 / 서울오피스 / 1월
```

### 1차 LLM 해석

```json
{
  "activity": "electricity",
  "amount": 1200,
  "unit": "kWh",
  "site": "Seoul office",
  "period": "January"
}
```

### Compiler tool 결과

```json
{
  "status": "blocked",
  "passed": ["activity", "amount", "site"],
  "unknown": ["period.year"],
  "failed": [
    {
      "field": "unit",
      "reason": "missing_source_witness",
      "claimed_value": "kWh"
    }
  ],
  "obligations": [
    "find_unit_source_or_mark_missing_unit",
    "find_reporting_year_context"
  ]
}
```

### 2차 LLM 해석

LLM은 compiler report를 보고 해석을 수정한다.

```json
{
  "activity": "electricity",
  "amount": 1200,
  "unit": null,
  "site": "Seoul office",
  "period": "2024-01",
  "hazards": ["missing_unit"]
}
```

### Compiler tool 결과

```json
{
  "status": "review_required",
  "passed": ["activity", "amount", "site", "period"],
  "failed": [],
  "hazards": ["missing_unit"],
  "can_project_public_row": false,
  "can_project_review_item": true
}
```

이 결과는 실패가 아니다. LLM이 과잉 추론을 제거했고, 컴파일러가 review 가능한 상태를 확인했다.

---

## 8. LLM이 compiler report를 다루는 규칙

LLM은 compiler status를 낮출 수 없다.

```text
compiler failed claim은 public claim으로 사용할 수 없다.
compiler unknown claim은 확정 표현으로 사용할 수 없다.
compiler unchecked area는 rule acquisition 또는 review로 보내야 한다.
LLM은 receipt를 위조할 수 없다.
LLM은 hard invariant를 완화할 수 없다.
```

금지되는 행동:

```text
LLM-only value를 commit 가능하게 만들기
source witness requirement 완화
CommitReceipt 없이 PublicRow 생성
row.status를 commit truth로 복원
특정 케이스만 통과시키는 ad hoc patch 생성
```

---

## 9. Rule acquisition과의 연결

`unchecked` 또는 `missing_rule_coverage`가 나오면 LLM은 rule acquisition 경로로 이동할 수 있다.

```text
Compiler:
  factor_period_compatibility has no active rule.

LLM:
  factor version과 period의 호환성을 검사하는 compatibility rule template이 필요하다.

Rule proposal:
  period must be covered by factor.valid_period.

Rule compiler:
  schema/type/hard invariant/test를 검사한다.
```

중요한 점은 LLM이 룰을 직접 활성화하지 않는다는 것이다.

```text
LLM proposes rule.
Rule compiler validates rule.
RuleReceipt records rule origin.
Only accepted rules affect future compiler reports.
```

---

## 10. Canonical sentence inspection과의 연결

Compiler tool은 artifact를 canonical sentence로 렌더링할 수 있다.

예시:

```text
Candidate C1 claims that Seoul office used 1,200 kWh of electricity in January.
```

LLM은 이 문장을 원본 evidence와 비교해 다음 semantic issue를 찾을 수 있다.

```text
unsupported assertion
overstated claim
missing context
contradiction
ambiguous reading
missing rule
```

LLM의 sentence inspection 결과도 직접 truth가 아니다. 다시 compiler hazard로 컴파일되어야 한다.

```text
LLM semantic issue
→ SemanticIssue artifact
→ compiler hazard
→ judgment / review / receipt
```

---

## 11. 완료 조건

이 루프의 완료는 LLM의 확신으로 정하지 않는다.

완료 조건은 compiler report와 receipt precondition으로 판단한다.

```text
blocking diagnostic이 없다.
public field가 source witness를 가진다.
unknown이 public claim으로 남아 있지 않다.
unchecked area가 active rule, review, 또는 known limitation으로 처리됐다.
receipt precondition이 충족된다.
새 iteration에서 의미 있는 obligation이 추가되지 않는다.
```

중요한 점:

```text
완성된 컴파일러 = 보편적으로 완전한 컴파일러가 아니다.
완성된 해석 = 현재 corpus/scope에서 obligations가 해소된 interpretation이다.
```

---

## 12. 첫 구현 slice

첫 코드 PR은 전체 agent를 만들 필요가 없다.

가장 작은 slice는 다음과 같다.

```text
InterpretationHypothesis
→ CompilerTool.compile_interpretation(...)
→ CompileReport
→ obligations
→ revised InterpretationHypothesis fixture
→ second CompileReport
```

첫 테스트 목표:

```text
LLM이 제안한 unsupported unit은 compile report에서 failed claim이 된다.
Compiler report는 find_source_witness obligation을 반환한다.
수정된 hypothesis가 unit을 확정하지 않으면 review_required 상태가 된다.
Public projection은 CommitReceipt 없이는 생성되지 않는다.
```

예상 테스트 이름:

```text
tests/test_llm_orchestrated_compiler_tool_loop.py
```

---

## 13. Non-goals

이 문서는 계획 문서다. 다음은 이 문서의 범위가 아니다.

```text
LLM API 연결
agent framework 선택
legacy pipeline 교체
GovernancePass 수정
PublicRow 생성 로직 변경
Rule acquisition 구현
canonical sentence inspector 구현
```

또한 이 문서는 LLM을 public truth authority로 승격하지 않는다.

---

## 14. 요약

```text
LLM is the interpreter.
Compiler is the obligation oracle.
Receipt is the public truth boundary.
```

이 설계의 목적은 LLM이 자유롭게 row를 만들게 하는 것이 아니다.

목적은 다음과 같다.

```text
LLM이 넓게 해석한다.
Compiler tool이 그 해석의 증명 채무를 산출한다.
LLM이 채무를 해결하기 위해 evidence/rule/context를 찾는다.
Compiler tool이 다시 검사한다.
Receipt가 안정화된 결과만 public boundary로 통과시킨다.
```
