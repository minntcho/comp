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
표면은 validation handoff 전 material, policy effect, scoped grant,
conflict resolver, policy assembly, selection decision, decision ledger,
selected validation contract, shadow policy comparison을 설명하기 위한 것이다.
validation authority, receipt authority, replay authority가 아니다.

```python
from comp.policy import MaterialDescriptor, PolicyEffect
from comp.policy import PolicyAssembly, PolicyAssemblySubject, ConflictResolver
from comp.policy import ScopedGrant, SelectionDecision, DecisionLedger
from comp.policy import SelectedValidationContract
from comp.policy import ShadowPolicyComparison, policy_artifact_digest
```

`PolicyAssembly` can assemble a `DecisionLedger` and matching
`SelectedValidationContract` together, while keeping both artifacts
pre-validation and non-authoritative.
Pipeline scope changes are represented only by `grant_scope` or
`restrict_scope` `PolicyEffect`s; status effects such as `select` and `hold`
do not carry scope.
`policy_artifact_digest(...)`, `DecisionLedger.digest()`, and
`SelectedValidationContract.digest()`, and `ShadowPolicyComparison.digest()`
provide stable audit identifiers only; they are not receipt authority or replay
proof.
`ShadowPolicyComparison` can compare actual and counterfactual policy outputs
by selected, held, rejected, and projection-candidate deltas. It is audit
material only and cannot compile, mint receipts, replay, or authorize public
projection.

`comp.runtime.ValidationHandoff`는 selected validation contract를
`InterpretationHypothesis`로 옮기는 얇은 runtime bridge다. contract에 포함된
selected decision만 compiler-facing hypothesis로 넘길 수 있고, selected
decision target snapshot이 있으면 claim field와도 맞아야 한다. It has no
compile, commit, receipt, or replay authority.

```python
from comp.runtime import ValidationHandoff, ValidationHandoffClaim
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

작업 시작 전에 이 순서로 현재 authority를 확인한다.

```text
docs/index.md
docs/architecture/document-governance.md
docs/architecture/contracts/policy-boundary.md
docs/architecture/maps/policy-assembled-trust-kernel.md
```

역할은 대략 이렇다.

```text
docs/index.md
  현재 architecture 문서의 navigation source of truth다. 새 작업은 먼저
  Active Contracts, Implementation Maps, North Stars 중 어떤 면을 건드리는지
  여기서 찾는다.

document-governance
  어떤 문서가 PR을 막을 수 있는지, status와 위치가 어떻게 맞아야 하는지,
  docs/index.md와 문서 header가 각각 어떤 authority를 갖는지 정의한다.

policy-boundary
  pre-validation policy가 할 수 있는 일과 할 수 없는 일을 고정하는 active
  contract다. Policy may shape validation input. Policy may not validate.
  Policy may not authorize public projection. Policy may not replace replay.

policy-assembled-trust-kernel
  policy-boundary를 넘지 않는 선에서 MaterialDescriptor, PolicyEffect,
  scoped grant, decision ledger, selected validation contract가 어떻게 조립될 수
  있는지 설명하는 implementation map이다.
```

현재 policy 이행축은 broad framework를 한 번에 세우는 것이 아니다.
새 policy work는 `comp.policy`처럼 작은 pre-validation vocabulary slice에서 시작한다.
그 slice는 validation handoff 전 material과 policy effect를 설명할 수 있지만,
compiler validation, receipt authority, replay authority를 대신하지 않는다.

작업 영역별로 추가 확인할 문서는 `docs/index.md`에서 찾는다.

```text
compiler / receipt authority
  docs/architecture/contracts/compiler-domain-boundary.md
  docs/architecture/contracts/trust-kernel-extension-rings.md
  docs/api/public-output-gate.md

persistence / replay material
  docs/architecture/contracts/artifact-envelope-builder.md
  docs/architecture/contracts/persistence-ledger-boundary.md

agent / LLM assistance
  docs/architecture/contracts/memory-assisted-compiler-loop.md
  docs/architecture/north-stars/llm-worker-orchestration.md
```

archive 문서는 current guidance가 아니다. 과거 판단, migration context, 왜 어떤
길을 버렸는지 확인할 때만 사용한다.

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
