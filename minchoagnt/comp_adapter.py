from __future__ import annotations

from dataclasses import dataclass, field

from comp.compiler_tool import (
    CompileReport,
    CompilerTool,
    InterpretationHypothesis,
    compile_report_to_facts,
)
from comp.judgment import CommitReceipt, Fact, JudgmentState, SubjectRef


@dataclass(frozen=True)
class CompCompileResult:
    hypothesis: InterpretationHypothesis
    subject: SubjectRef
    report: CompileReport
    judgment: JudgmentState = field(default_factory=JudgmentState)
    receipt: CommitReceipt | None = None


class CompCompilerAdapter:
    """Agent-side adapter for calling comp without gaining comp authority."""

    def __init__(
        self,
        compiler: CompilerTool | None = None,
        *,
        allowed_units: frozenset[str] | None = None,
        known_fields: frozenset[str] | None = None,
    ):
        if compiler is not None:
            self.compiler = compiler
            return

        options = {}
        if allowed_units is not None:
            options["allowed_units"] = allowed_units
        if known_fields is not None:
            options["known_fields"] = known_fields
        self.compiler = CompilerTool(**options)

    def compile(self, hypothesis: InterpretationHypothesis) -> CompCompileResult:
        subject = SubjectRef("claim", hypothesis.hypothesis_id)
        report = self.compiler.compile_interpretation(hypothesis)
        return CompCompileResult(
            hypothesis=hypothesis,
            subject=subject,
            report=report,
        )

    def record(self, result: CompCompileResult) -> set[Fact]:
        facts = compile_report_to_facts(result.report, result.subject)
        return result.judgment.add_facts(facts)


__all__ = ["CompCompileResult", "CompCompilerAdapter"]
