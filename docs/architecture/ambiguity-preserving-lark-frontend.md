# Ambiguity-Preserving Lark Evidence Frontend

이 문서는 `comp` rebuild branch에서 Lark를 어떻게 사용할지 정의하는 아키텍처 제안이다.

핵심은 Lark를 단순 DSL parser로만 쓰지 않고, raw fragment에서 가능한 해석 후보를 보존하는 **evidence frontend**로 활용하는 것이다.

다만 이 문서는 Lark를 source of truth로 승격하지 않는다. 장기 권위는 여전히 다음 계층에 있다.

```text
Evidence-backed Judgment
Governance Decision
Receipt Ledger
```

Lark는 이 구조 앞단에서 후보를 만든다. 판단하지 않는다.

---

## 1. 핵심 원칙

```text
Parsing must not decide truth.
Parsing only enumerates structurally valid interpretations.
```

즉 parser의 역할은 정답 AST 하나를 고르는 것이 아니다.

Parser는 raw fragment가 어떤 claim 구조로 읽힐 수 있는지 가능한 해석을 드러낸다. 그중 무엇이 선택되어야 하는지는 Judgment Kernel의 책임이다.

짧게 쓰면 다음과 같다.

```text
Lark preserves ambiguity.
Judgment resolves ambiguity.
Receipt proves the resolution.
Projection renders it.
```

---

## 2. 왜 필요한가

기존 legacy pipeline은 대략 다음 흐름을 가진다.

```text
DSL
→ ProgramSpec / CompiledProgramSpec
→ fragments
→ LexPass
→ ParsePass
→ ScopeResolutionPass
→ InferencePass
→ SemanticPass
→ RepairPass
→ EmitPass
→ GovernancePass
→ CalculationPass
→ rows / merge_log / calculations / event_log
```

이 구조의 문제는 raw input의 애매함이 명시적인 architectural object로 남지 않는다는 점이다.

예를 들어 같은 fragment에서 여러 해석이 가능할 때, legacy pipeline은 어느 시점에서 `active_claim_id`, `shadow_claim_ids`, `frame.status`, `row.status` 같은 runtime 상태로 그 애매함을 흡수한다.

그 결과 다음 질문에 답하기 어려워진다.

```text
이 값은 어떤 해석 후보들 중 선택된 것인가?
선택되지 않은 후보는 무엇인가?
선택은 parser가 한 것인가, judgment가 한 것인가?
선택 근거는 receipt에 남는가?
row가 나오기 전에 commit barrier를 통과했는가?
```

새 구조에서는 ambiguity 자체를 숨기지 않는다.

```text
ambiguity
→ candidate frontier
→ judgment selection
→ selection receipt
→ governance decision
→ commit receipt
→ public projection
```

즉 애매함은 버그가 아니라 evidence의 일부다.

---

## 3. 아키텍처상 위치

이 설계는 전체 architecture가 아니다.

전체 architecture는 receipt-backed judgment architecture다.

```text
raw fragment
→ evidence / claim
→ judgment
→ governance decision
→ receipt
→ public projection
```

이 문서의 범위는 그중 앞단이다.

```text
raw fragment
→ ambiguity-preserving Lark frontend
→ ClaimCandidate facts
```

그 뒤는 기존 authority map의 소유권을 따른다.

```text
ClaimCandidate facts
→ Judgment Kernel
→ SelectionReceipt
→ GovernanceDecision
→ CommitReceipt
→ PublicProjection
```

따라서 Lark frontend의 권한은 여기까지다.

```text
할 수 있음:
- raw fragment를 parse한다.
- 가능한 parse derivation들을 보존한다.
- derivation을 ClaimCandidate fact로 변환한다.
- span, source, rule provenance를 붙인다.

하면 안 됨:
- winning claim을 고른다.
- active/shadow 상태를 확정한다.
- governance decision을 만든다.
- CommitReceipt 없이 public row를 만든다.
- row.status를 commit truth처럼 사용한다.
```

---

## 4. 기존 Lark 사용 방식과 새 사용 방식

기존에 Lark는 주로 DSL spec을 읽는 데 쓰인다.

```text
esgdl.lark
→ ASTBuilder
→ Lowerer
→ ProgramSpec
→ legacy passes
```

이 방식에서 Lark는 `esgdl`이라는 specification language를 parse한다.

새 제안은 여기에 한 단계를 추가한다.

```text
Level 1: ESGDL parser
  esgdl.lark → ProgramSpec

Level 2: Evidence grammar generator
  ProgramSpec → generated Lark grammar

Level 3: Ambiguous fragment parser
  raw fragment → parse forest / _ambig tree

Level 4: Judgment facts
  parse derivations → ClaimCandidate facts

Level 5: Receipt-backed projection
  selected derivation → judgment → governance → receipt → public row
```

즉 다음과 같이 바뀐다.

```text
기존:
Lark parses the DSL.

신규:
Lark parses the DSL,
then the DSL generates another Lark grammar
that parses raw evidence fragments.
```

---

## 5. 제안 흐름

전체 frontend 흐름은 다음과 같다.

```text
ESGDL Spec
  ↓
Deterministic DSL Parser
  ↓
ProgramSpec
  ↓
Evidence Grammar Compiler
  ↓
Generated Fragment Grammar
  ↓
Lark Earley Parse Forest
  ↓
Parse Derivations
  ↓
ClaimCandidate Facts
  ↓
Judgment Kernel
```

이때 중요한 점은 `ClaimCandidate`가 아직 truth가 아니라는 것이다.

`ClaimCandidate`는 다음 의미만 가진다.

```text
이 raw fragment는 이 claim 구조로 읽힐 수 있다.
```

반대로 다음 의미는 가지면 안 된다.

```text
이 claim이 선택됐다.
이 claim이 공개 가능하다.
이 claim에서 row를 만들어도 된다.
```

---

## 6. Ambiguity를 evidence로 보는 방식

예를 들어 입력 fragment가 다음과 같다고 하자.

```text
Electricity 1,200 kWh 2024 Seoul office
```

legacy pipeline에서는 token과 frame slot을 만든 뒤 어느 시점에서 active/shadow를 정한다.

새 구조에서는 일부러 여러 해석을 보존한다.

```text
parse A:
  activity = Electricity
  amount = 1200
  unit = kWh
  period = 2024
  site = Seoul office

parse B:
  activity = Electricity
  amount = 1200
  unit = kWh
  period = unknown
  site = 2024 Seoul office

parse C:
  activity = Electricity
  amount = 1200
  unit = kWh
  site = Seoul office
  note = 2024
```

Lark frontend는 이것들을 `_ambig` tree 또는 parse forest에서 꺼내 `ClaimCandidate`로 변환한다.

```text
_ambig
  observation_parse_A
  observation_parse_B
  observation_parse_C
```

그다음 Judgment Kernel이 선택한다.

```text
selected_derivation = parse_A
reason_codes = [
  "period_pattern_detected",
  "site_context_supported",
  "unit_activity_compatible"
]
```

그리고 선택은 receipt로 남는다.

```text
SelectionReceipt
  selected_candidate_id
  rejected_candidate_ids
  parse_derivation_id
  evidence_span
  reason_codes
```

이 구조에서는 ambiguity가 pass 내부 상태로 숨어 있지 않고, 판단 가능한 후보 집합으로 노출된다.

---

## 7. Parser mode 정책

Lark 사용 mode는 입력 종류에 따라 분리한다.

### 7.1 ESGDL spec mode

ESGDL은 사람이 작성하는 specification language다.

여기서는 ambiguity를 늘리는 것보다 deterministic compile error가 중요하다.

```text
parser = "lalr"
lexer = "contextual"
strict = true
propagate_positions = true
```

목표:

```text
- spec 문법 오류를 빠르게 찾는다.
- rule/source 위치를 보존한다.
- DSL rule provenance를 나중에 receipt/debug trace에 연결한다.
```

### 7.2 Fragment normal mode

일반 raw fragment는 애매할 수 있다.

```text
parser = "earley"
lexer = "dynamic"
ambiguity = "explicit"
propagate_positions = true
```

목표:

```text
- 구조적으로 가능한 해석을 보존한다.
- 하나의 정답 AST를 강제로 고르지 않는다.
- _ambig tree를 ClaimCandidate로 변환한다.
```

### 7.3 Dirty repair mode

`dynamic_complete`는 기본값으로 쓰지 않는다.

이 mode는 매우 짧은 fragment나 normal mode 실패 case에만 제한적으로 사용한다.

```text
parser = "earley"
lexer = "dynamic_complete"
ambiguity = "explicit"
```

사용 조건:

```text
- fragment 길이가 짧다.
- normal mode가 실패했다.
- open-ended regex가 없다.
- ambiguity budget 안에 들어온다.
```

금지:

```text
- 전체 문서에 dynamic_complete 적용
- 긴 table dump에 dynamic_complete 적용
- /.*/ 같은 unbounded terminal과 함께 사용
```

---

## 8. Generated evidence grammar

ESGDL의 일부 선언은 fragment grammar로 compile될 수 있다.

예시 DSL:

```text
token AMOUNT := number()
token UNIT := "kWh" | "MWh"

parser ElectricityUse on cell {
  build ActivityObservation
  bind amount from AMOUNT
  bind unit from UNIT
}
```

생성 grammar의 예시는 다음과 같다.

```lark
start: observation+

?observation: electricity_use

electricity_use: AMOUNT GAP? UNIT -> activity_observation

AMOUNT: /-?[0-9]+(,[0-9]{3})*(\.[0-9]+)?|-?[0-9]+(\.[0-9]+)?/
UNIT: "kWh" | "MWh"
GAP: /[\s,:;-]+/

%ignore /[^\S\n]+/
```

이 grammar는 final truth를 만들지 않는다.

이 grammar는 다음만 만든다.

```text
ActivityObservation 후보로 읽을 수 있는 구조
```

---

## 9. ClaimCandidate fact sketch

초기 구현에서는 다음 정도의 구조를 생각할 수 있다.

```python
@dataclass(frozen=True)
class ClaimCandidate:
    candidate_id: str
    subject_id: str
    frame_type: str
    slot_values: Mapping[str, object]
    evidence_span: Span
    derivation_id: str
    grammar_rule_id: str | None
    source_fragment_id: str
    confidence_hint: float | None = None
```

주의할 점:

```text
confidence_hint는 judgment가 아니다.
state="active" 같은 필드는 frontend에 두지 않는다.
```

Frontend가 만들어도 되는 것은 후보와 provenance다.

Frontend가 만들면 안 되는 것은 선택 상태다.

---

## 10. LLM/fallback의 위치

LLM fallback을 쓰더라도 judgment로 쓰지 않는다.

LLM은 다음 역할만 가진다.

```text
candidate token proposer
candidate span proposer
candidate label proposer
```

LLM이 직접 다음을 결정하면 안 된다.

```text
winning claim
commit decision
public row
```

권장 흐름:

```text
raw text
→ deterministic regex candidates
→ fallback LLM candidates
→ EvidenceToken stream
→ Lark structural parser
→ ClaimCandidate facts
→ Judgment Kernel
```

즉 LLM은 후보를 제안하고, Lark는 구조적 호환성을 검사하고, Judgment가 선택한다.

이렇게 하면 LLM을 쓰더라도 authority boundary가 흐려지지 않는다.

---

## 11. Governance와 Lark의 관계

나중에 governance fact stream을 grammar로 검증하는 실험은 가능하다.

예시:

```text
FACT selected(activity)
FACT selected(amount)
FACT selected(unit)
FACT evidence(amount)
FACT no_open_hazard(unit)
FACT policy_allowed(scope1)
```

이런 fact stream을 grammar로 parse해서 `commit`, `hold`, `reject`를 설명할 수 있다.

하지만 이것은 1차 목표가 아니다.

초기 설계에서는 governance를 Lark frontend 범위 밖에 둔다.

```text
PR1:
  Lark evidence frontend

Later spike:
  governance fact grammar
```

이유:

```text
- Governance는 commit authority에 가깝다.
- Lark frontend가 governance authority를 먹으면 안 된다.
- 우선 raw evidence ambiguity 보존만 검증해야 한다.
```

---

## 12. Projection contract

Public row는 CommitReceipt 없이 생성되면 안 된다.

Frontend는 다음을 만들지 않는다.

```text
PublicRow
CSV row
JSON output
DataFrame view
```

Projection layer의 입력은 raw parse tree가 아니라 committed receipt여야 한다.

```text
CommitReceipt
→ PublicProjection
```

따라서 다음은 금지다.

```text
Lark parse tree
→ row
```

허용되는 흐름은 다음뿐이다.

```text
Lark parse tree
→ ClaimCandidate
→ Judgment
→ GovernanceDecision
→ CommitReceipt
→ PublicProjection
```

---

## 13. Risk controls

Ambiguous parsing은 강력하지만 위험하다.

특히 ESG-style fragment는 다음 특징을 가진다.

```text
- delimiter가 약하다.
- 숫자와 단위가 많다.
- site, period, activity가 섞인다.
- table cell과 문장이 섞인다.
- 같은 token이 여러 role로 해석될 수 있다.
```

따라서 grammar compiler에는 budget이 필요하다.

초기 guardrail:

```text
max_fragment_chars
max_candidates_per_fragment
max_ambiguity_nodes
max_derivations_to_materialize
parse_timeout_ms
forbid_unbounded_gap
forbid_dot_star_terminals_by_default
```

특히 다음 terminal은 기본 금지한다.

```lark
GAP: /.*/
VALUE: /.*/
ANYTHING: /.+/
```

이런 terminal은 ambiguity explosion을 만들 수 있다.

---

## 14. 첫 vertical slice

첫 구현 PR은 legacy pipeline 전체를 교체하지 않는다.

목표는 작게 잡는다.

```text
ESGDL spec
→ generated fragment grammar
→ ambiguous fragment parse
→ two or more ClaimCandidate facts
→ no public row before CommitReceipt
```

테스트 이름 예시:

```text
tests/test_lark_ambiguity_to_claim_candidates.py
```

테스트가 검증해야 할 것:

```text
1. ambiguous fragment에서 후보가 2개 이상 생성된다.
2. 모든 후보는 evidence span을 가진다.
3. 모든 후보는 derivation id를 가진다.
4. frontend는 active candidate를 정하지 않는다.
5. frontend는 public row를 만들지 않는다.
```

예시 assertion:

```python
assert len(candidates) >= 2
assert all(c.evidence_span is not None for c in candidates)
assert all(c.derivation_id is not None for c in candidates)
assert not any(c.state == "active" for c in candidates)
assert not any(c.kind == "public_row" for c in candidates)
```

`state == "active"` 같은 구조 자체를 만들지 않는 것이 더 좋다.

---

## 15. Suggested module shape

초기 구조는 다음 정도면 충분하다.

```text
comp/
  dsl/
    esgdl.lark
    parser.py
    ast.py
    lower.py

  evidence_frontend/
    grammar_compiler.py
    fragment_parser.py
    derivations.py
    candidates.py

  judgment/
    core.py
    engine.py
    frontier.py
    receipts.py

  governance/
    decision.py

  receipts/
    ledger.py

  projection/
    public_row.py

  adapters/
    legacy/
      token_occurrence_adapter.py
      compile_artifacts_adapter.py
```

첫 PR에서 이 전체를 만들 필요는 없다.

첫 code PR은 다음 정도로 제한한다.

```text
comp/evidence_frontend/grammar_compiler.py
comp/evidence_frontend/fragment_parser.py
comp/evidence_frontend/derivations.py
comp/evidence_frontend/candidates.py
tests/test_lark_ambiguity_to_claim_candidates.py
```

---

## 16. PR sequencing

권장 순서:

```text
PR1 docs:
  ambiguity-preserving Lark evidence frontend design

PR2 code spike:
  generated grammar + _ambig tree → ClaimCandidate

PR3 judgment integration:
  ClaimCandidate facts → Judgment Kernel → SelectionReceipt

PR4 commit boundary:
  GovernanceDecision → CommitReceipt → PublicProjection

PR5 optional spike:
  object-stream lexer / fallback token adapter

PR6 optional spike:
  governance fact grammar
```

순서를 바꾸면 안 되는 이유:

```text
- 먼저 후보 생성과 judgment boundary를 분리해야 한다.
- 그다음 selection receipt를 붙여야 한다.
- 그다음 public projection을 receipt 뒤로 밀어야 한다.
```

---

## 17. Non-goals

이 문서는 다음을 하지 않는다.

```text
- legacy pipeline 전체 교체
- GovernancePass 수정
- row.status 의미 변경
- CalculationPass 연결
- dynamic_complete 기본값 채택
- LLM fallback을 judgment authority로 승격
- generated parser에서 public row 생성
- CommitReceipt 없이 projection 허용
```

이 문서의 목적은 한 가지다.

```text
raw fragment의 ambiguity를 first-class evidence candidate로 끌어올린다.
```

---

## 18. 최종 요약

이 설계는 Lark를 더 많이 쓰자는 제안이 아니다.

정확히는 다음 제안이다.

```text
Lark를 truth-deciding parser가 아니라
ambiguity-preserving evidence frontend로 사용한다.
```

최종 규칙:

```text
Lark preserves ambiguity.
Judgment resolves ambiguity.
Receipt proves the resolution.
Projection renders it.
```

이 규칙을 지키면 legacy pipeline의 문제였던 다음 흐름을 피할 수 있다.

```text
parse 단계에서 active/shadow를 너무 일찍 정함
row.status가 commit truth처럼 행동함
governance가 row를 직접 mutate함
receipt가 row metadata에 묻힘
```

따라서 이 frontend 설계는 기존 authority map을 대체하지 않는다.

오히려 authority map을 지키기 위해 raw evidence를 더 정직하게 Judgment Kernel 앞에 올려놓는 장치다.
