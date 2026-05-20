# Active Surface Cutover Plan

Status: historical-note
Owner: docs
Last checked against code: 2026-05-20
Can block PRs: no

이 문서는 rebuild branch에서 **active package surface**를 legacy pipeline에서 judgment/compiler-tool loop 중심으로 전환하는 첫 번째 cutover 기준을 정의한다.

이 문서의 목적은 legacy 파일을 즉시 삭제하는 것이 아니다. 목적은 다음을 명확히 하는 것이다.

```text
무엇이 현재 active surface인가?
무엇이 legacy/archive 후보인가?
어떤 import path가 새 아키텍처의 public contract인가?
```

---

## 1. 결론

`comp` top-level package는 더 이상 legacy runner facade를 대표하지 않는다.

기존 top-level surface는 다음을 노출했다.

```text
ESGPipelineRunner
CompiledESGPipelineRunner
PipelineResources
PipelineRunResult
compile_program_spec
load_program_spec_from_dsl
load_compiled_program_spec_from_dsl
```

이들은 legacy pass pipeline을 실행하기 위한 surface다.

rebuild branch의 active direction은 다음이다.

```text
Evidence-backed Judgment
Compiler Tool Report / Obligations
Governance Decision
Receipt Ledger
Projection Boundary
```

따라서 top-level `comp`는 legacy runner가 아니라 **judgment core와 이후 compiler-tool loop의 진입면**을 대표해야 한다.

---

## 2. PR1 범위

PR1은 작은 cutover다.

```text
1. top-level `comp`에서 legacy runner export를 제거한다.
2. top-level `comp`는 judgment-core exports만 노출한다.
3. README에 active package surface를 명시한다.
4. package smoke test를 새 active surface 기준으로 바꾼다.
```

PR1에서 하지 않는 것:

```text
legacy 파일 삭제
legacy pipeline 이동
pyproject.py-modules 제거
GovernancePass 수정
row.status 의미 변경
LLM API 연결
CompilerTool 구현
```

---

## 3. Active surface

PR1 이후 active top-level surface는 judgment core다.

```text
Fact
FactTag
SubjectRef
SubjectKind
JudgmentState
FixpointEngine
CandidateSummary
frontier
winner_or_none
needs_review
DraftSnapshot
CommitSpec
ProjectionSpec
CompiledJudgmentProgram
TransferRule
SelectionReceipt
CommitReceipt
committable
project_public_row
```

이 surface는 새 architecture의 최소 기반이다.

```text
LLM Agent
→ InterpretationHypothesis
→ Compiler Tool
→ CompileReport / Obligations
→ Judgment Facts
→ Governance Decision
→ Receipt
→ Projection
```

PR1은 아직 `InterpretationHypothesis`나 `CompileReport`를 추가하지 않는다. 그 작업은 다음 PR의 대상이다.

---

## 4. Legacy/archive 후보

다음은 active surface가 아니라 archive 후보로 본다.

```text
CompileArtifacts
LexPass
ParsePass
ScopeResolutionPass
InferencePass
SemanticPass
RepairPass
EmitPass
GovernancePass
CalculationPass
ESGPipelineRunner
CompiledESGPipelineRunner
legacy event_log / merge_log 중심 tests
```

이들은 바로 삭제하지 않는다. 하지만 장기 authority boundary로 승격하지 않는다.

이 판단은 현재 active architecture 문서의 legacy authority 경계와 연결된다.

```text
row.status as commit truth
GovernancePass as direct row mutator
CompileArtifacts as kernel state
pass-owned semantic authority
legacy/package parity as architecture success
```

---

## 5. Import policy

새 코드에서는 다음을 선호한다.

```python
from comp import Fact, JudgmentState, SubjectRef
from comp.judgment import SelectionReceipt, CommitReceipt
```

legacy runner가 필요한 과거 테스트나 reference material은 archive snapshot을 사용한다.

```text
legacy/archive/pipeline_legacy_20260518/
```

`comp.runner`, pass exports, root legacy modules, and legacy DSL/eval/builtin
facades are not active package source after PR4c.

---

## 6. 다음 PR

PR2는 다음 중 하나로 간다.

```text
A. legacy pipeline archive 이동
B. CompilerTool / CompileReport 최소 slice 추가
```

권장 순서는 다음이다.

```text
PR1: active top-level surface cutover
PR2: CompilerTool report contract
PR3: legacy pipeline archive move
PR4: report → judgment facts adapter
```

PR2에서 만들어야 할 최소 모델은 다음이다.

```text
InterpretationHypothesis
ClaimHypothesis
EvidenceWitness
CompileReport
CheckedClaim
FailedClaim
UnknownClaim
UncheckedArea
ProofObligation
Hazard
```

---

## 7. Success criteria

PR1은 다음을 만족하면 된다.

```text
`from comp import Fact, JudgmentState, SubjectRef`가 가능하다.
`from comp import ESGPipelineRunner`는 더 이상 active contract가 아니다.
package smoke test가 judgment-core surface 기준으로 갱신된다.
legacy runner 파일은 active source tree에서 내려가고 archive snapshot에 남는다.
README가 active surface 기준을 설명한다.
```
