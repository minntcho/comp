# comp

`comp`는 receipt-gated proof package compiler다.

현재 방향은 ESG 전용 DSL 컴파일러도, row generator도 아니다. 핵심은
evidence를 보존하고, obligation을 드러내고, reference를 canonical하게
bind하고, 계산 결과를 traceable claim으로 만들고, 마지막 공개는 receipt
authority를 통해서만 허가하는 것이다.

## 현재 흐름

```text
candidate / obligation / judgment / reference / calculation
-> ReviewPackage
-> ReviewDecision
-> PublicOutputReceipt
-> Judgment Facts
-> receipt-gated projection
```

중요한 권한 경계:

```text
ReferenceOption != CanonicalReference
CalculatedClaim != public output
ReviewPackage != public authority
ReviewDecision != public authority
PublicOutputReceipt == projection gate
```

## 5-minute quickstart: receipt 없이는 공개되지 않는다

<!-- compiler-tool-quickstart:start -->
```python
from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from comp.compiler_tool import (
    ClaimCandidate,
    CompilerTool,
    EvidenceRef,
    InterpretationHypothesis,
    prepare_commit,
)

hypothesis = InterpretationHypothesis(
    hypothesis_id="hyp-1",
    subject_id="facility-1",
    claims=(
        ClaimCandidate(field="amount", value=1200, witness_id="span-amount"),
        ClaimCandidate(field="unit", value="kWh", witness_id="span-unit"),
    ),
    witnesses=(
        EvidenceRef(
            witness_id="span-amount",
            field="amount",
            source="invoice.pdf",
            span="p1: electricity amount",
        ),
        EvidenceRef(
            witness_id="span-unit",
            field="unit",
            source="invoice.pdf",
            span="p1: electricity unit",
        ),
    ),
)

report = CompilerTool(
    known_fields=frozenset({"amount", "unit"}),
    allowed_units=frozenset({"kWh"}),
).compile_interpretation(hypothesis)

assert report.status == "accepted"
assert report.can_build_public_output is False

projection = PublicOutputSpec("public-row", ("amount", "unit"))
source_row = {
    "amount": 1200,
    "unit": "kWh",
    "internal_note": "operator note, not public",
}

blocked_without_receipt = False
try:
    build_public_output(source_row, projection)
except PublicOutputBlocked:
    blocked_without_receipt = True

assert blocked_without_receipt is True

preparation = prepare_commit(
    report,
    subject_id="facility-1",
    public_row_id="public-row-1",
    projection_id="public-row",
)

assert preparation.receipt is not None

row = build_public_output(source_row, projection, receipt=preparation.receipt)

assert row == {"amount": 1200, "unit": "kWh"}
assert "internal_note" not in row
```
<!-- compiler-tool-quickstart:end -->

`CompilerTool`은 후보 claim과 evidence 위치를 `ValidationReport`로 바꾼다.
`ValidationReport`가 accepted여도 공개 권한은 없다. `prepare_commit(...)`이
clean package와 commit decision을 확인해 `PublicOutputReceipt`를 만들 때만
`build_public_output(...)`이 통과한다.

embedding과 LLM도 같은 원칙을 따른다.

```text
Embedding = recall fabric
LLM = resolver artifact proposer
Compiler = artifact / binding gate
DB = typed canonical reference authority
Receipt = public projection authority
```

즉 embedding은 후보를 찾고, LLM은 obligation 해결용 artifact를 제출한다.
그 artifact가 실제로 obligation을 discharge하는지는 compiler gate가
판단한다.

## 활성 패키지 표면

top-level `comp` 패키지는 judgment-core surface를 노출한다.

```python
from comp import Fact, JudgmentState, SubjectRef
from comp import SelectionReceipt, PublicOutputReceipt
from comp import PublicOutputSpec, build_public_output
```

`comp.compiler_tool`은 현재 deterministic publication kernel surface를
노출한다.

```python
from comp.compiler_tool import CompilerTool, ValidationReport
from comp.compiler_tool import resolver_tasks_from_report
from comp.compiler_tool import prepare_commit, build_public_output_receipt
from comp.compiler_tool import compile_report_to_facts
```

`docs/api/compiler-tool.md` classifies this stable quickstart surface separately
from advanced and experimental helper exports. `comp.compiler_tool.__all__` is
an import-convenience surface, not the stability contract.

`comp.persistence`는 replayable artifact record와 receipt ledger surface를
노출한다. persisted row는 authority가 아니라 receipt로 재검증되어야 하는
view다.

```python
from comp.persistence import ArtifactEnvelope, InMemoryArtifactStore
from comp.persistence import InMemoryReceiptLedger
from comp.persistence import replay_public_projection
```

`comp.policy`는 pre-validation policy boundary vocabulary를 노출한다. 이
표면은 validation handoff 전 material과 policy effect를 설명하기 위한 것이며,
validation authority, receipt authority, replay authority가 아니다.

```python
from comp.policy import MaterialDescriptor, PolicyEffect
```

legacy pipeline runner, pass-pipeline module, compatibility facade는 active
package source가 아니다. 과거 pass-pipeline snapshot은 repository history에서만
확인하고, 현재 tree에는 reference copy를 유지하지 않는다.

## Compiler Tool 레이어

`comp.compiler_tool`은 의도적으로 레이어를 나눈다.

```text
semantic
  semantic judgment obligation
  submitted SemanticJudgment protocol validation

reference
  ReferenceOption
  deterministic selection
  canonical CanonicalReference

calculation
  CalculationRequirement
  CalculationTrace
  CalculatedClaim

resolver tasks
  ValidationRequirement -> ResolverTask
  resolver-facing task type, required artifact, payload

governance / commit
  ReviewPackage
  ReviewDecision
  PublicOutputReceipt builder
  CommitPreparation

judgment facts
  ValidationReport -> Fact
  CommitPreparation -> Fact
```

extractor, Lark, table parser, LLM hypothesis generator는 compiler 앞단의
candidate producer다. 이들은 checked claim, commit receipt, public
projection을 직접 만들면 안 된다.

`minchoagnt` 같은 agent layer는 compiler core 바깥에 있다. agent는
`ResolverTask`를 읽고 semantic judgment, reference query 같은 resolver
artifact를 제출할 수 있지만, commit receipt를 만들 권한은 없다.

## 문서 읽는 순서

현재 active architecture 문서는 여기서 시작한다.

```text
docs/index.md
docs/architecture/north-stars/retrieval-fabric-north-star.md
docs/architecture/maps/obligation-kernel-working-theory.md
docs/archive/architecture/llm-orchestrated-compiler-tool-loop.md
docs/architecture/contracts/memory-assisted-compiler-loop.md
```

역할은 대략 이렇다.

```text
retrieval-fabric-north-star
  embedding / retrieval / LLM resolver / reference DB의 장기 방향을 고정한다.

obligation-kernel-working-theory
  현재 구현 slice의 세부 working theory를 담는다.

llm-orchestrated-compiler-tool-loop
  LLM이 compiler diagnostic과 obligation을 어떻게 다루는지 설명한다.

memory-assisted-compiler-loop
  minchoagnt memory / skill loop가 obligation resolution을 어떻게 보조하는지 설명한다.
```

## 재구축 규칙

module을 옮기거나 키우기 전에 먼저 답해야 한다.

```text
이 module은 지금 어떤 authority를 갖고 있는가?
그 authority가 장기적으로 여기 있어야 하는가?
아니라면 어느 layer가 가져야 하는가?
```

답이 흐리면 relocation보다 architecture correction이 먼저다.

## PR contract gate

PR에서 확인해야 하는 최소 gate는 package smoke, unit tests, domain scenario
contract다. 로컬에서는 아래 명령으로 GitHub Actions와 같은 핵심 검증을
재현한다.

```bash
python -m pip install -e ".[test]"
python -m pytest -q
python -m tests.domain_scenarios list
python -m tests.domain_scenarios run-all
```
