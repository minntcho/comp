# comp

`comp` is a receipt-gated proof package compiler.

The active direction is no longer a domain-specific DSL-first compiler or a row generator.
The core work is to preserve evidence, expose obligations, bind references,
calculate derived claims, and only publish through receipt authority.

## Current Flow

```text
candidate / obligation / judgment / reference / calculation
-> CommitPackage
-> GovernanceDecision
-> CommitReceipt
-> Judgment Facts
-> receipt-gated projection
```

Important authority boundaries:

```text
DerivedClaim != public output
CommitPackage != public authority
GovernanceDecision != public authority
CommitReceipt == projection gate
```

## Active Package Surface

The top-level `comp` package exposes the judgment-core surface:

```python
from comp import Fact, JudgmentState, SubjectRef
from comp import SelectionReceipt, CommitReceipt
from comp import ProjectionSpec, project_public_row
```

The compiler-tool surface exposes the current deterministic kernel:

```python
from comp.compiler_tool import CompilerTool, CompileReport
from comp.compiler_tool import prepare_commit, build_commit_receipt
from comp.compiler_tool import compile_report_to_facts
```

Legacy pipeline runners, pass-pipeline modules, and compatibility facades are
archive reference material, not active package source.

## Compiler Tool Layers

`comp.compiler_tool` is intentionally layered:

```text
semantic
  semantic judgment obligations and submitted judgment validation

reference
  reference candidates, deterministic selection, and canonical bindings

calculation
  calculation requirements, calculation traces, and derived claims

governance / commit
  CommitPackage, GovernanceDecision, CommitReceipt builder, CommitPreparation

judgment facts
  adapters that publish compiler reports and commit preparation artifacts into
  JudgmentState as evidence, hazards, discharges, and provenance edges
```

Extractors such as Lark are candidate producers. They should produce evidence
and claim hypotheses for the compiler tool; they should not mint checked claims,
commit receipts, or public projections.

## Active Policy

Read these first:

```text
docs/architecture/authority-map.md
docs/architecture/kill-list.md
docs/architecture/obligation-kernel-working-theory.md
docs/architecture/llm-orchestrated-compiler-tool-loop.md
docs/architecture/memory-assisted-compiler-loop.md
```

These documents define the authority boundaries, the obligation/receipt kernel,
and how LLM or agent loops should interact with compiler diagnostics without
becoming public truth authority.

## Rebuild Rule

Before moving or expanding a module, answer:

```text
What authority does this module own today?
Should that authority stay here long term?
If not, which layer should own it?
```

Architecture correction comes before broad relocation.
