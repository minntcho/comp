from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from comp.compiler_tool import (
    CompileReport,
    CompilerTool,
    InterpretationHypothesis,
    ProofObligation,
    ReferenceCatalog,
    ReferenceResolver,
    RetrievalQueryPolicy,
    ResolverTask,
    SemanticJudgment,
    apply_semantic_judgments,
    compile_report_to_facts,
    reference_query_for_obligation_from_policy,
    reference_query_for_obligation_from_resolver_tasks,
    resolve_reference_search_obligations,
    resolve_reference_retrieval_obligations,
    resolver_task_from_obligation,
    resolver_tasks_from_report,
)
from comp.judgment import CommitReceipt, Fact, JudgmentState, SubjectRef


@dataclass(frozen=True)
class CompCompileResult:
    hypothesis: InterpretationHypothesis
    subject: SubjectRef
    report: CompileReport
    judgment: JudgmentState = field(default_factory=JudgmentState)
    receipt: CommitReceipt | None = None


@dataclass(frozen=True)
class CompResolutionResult:
    source: CompCompileResult
    result: CompCompileResult
    tasks: tuple[ResolverTask, ...] = field(default_factory=tuple)
    semantic_judgment_ids: tuple[str, ...] = field(default_factory=tuple)
    reference_query_obligation_ids: tuple[str, ...] = field(default_factory=tuple)


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

    def resolver_tasks(self, result: CompCompileResult) -> tuple[ResolverTask, ...]:
        return resolver_tasks_from_report(result.report)


class DeterministicCompResolver:
    """Fixture resolver for agent-side comp loops without LLM authority."""

    def __init__(
        self,
        *,
        semantic_judgments: Iterable[SemanticJudgment] = (),
        available_span_ids: Iterable[str] | None = None,
        reference_catalog: ReferenceCatalog | None = None,
        reference_resolver: ReferenceResolver | None = None,
        reference_queries: Mapping[str, str] | None = None,
        reference_query_policy: RetrievalQueryPolicy | None = None,
        reference_query_context: Mapping[str, Any] | None = None,
        reference_lens: str = "factor",
        reference_type: str | None = None,
        reference_limit: int = 10,
        retrieval_method: str = "keyword",
    ):
        self.semantic_judgments = tuple(semantic_judgments)
        self.available_span_ids = (
            None if available_span_ids is None else tuple(available_span_ids)
        )
        self.reference_catalog = reference_catalog
        self.reference_resolver = reference_resolver
        self.reference_queries = dict(reference_queries or {})
        self.reference_query_policy = reference_query_policy
        self.reference_query_context = dict(reference_query_context or {})
        self.reference_lens = reference_lens
        self.reference_type = reference_type
        self.reference_limit = reference_limit
        self.retrieval_method = retrieval_method

    def resolve(self, result: CompCompileResult) -> CompResolutionResult:
        tasks = resolver_tasks_from_report(result.report)
        report = result.report

        semantic_judgments = self._semantic_judgments_for(tasks)
        if semantic_judgments:
            report = apply_semantic_judgments(
                report,
                semantic_judgments,
                available_span_ids=self.available_span_ids,
            )

        if self.reference_resolver is not None:
            query_for_obligation = self._retrieval_query_for_obligation(tasks)
            reference_query_obligation_ids = (
                self._retrieval_query_obligation_ids(
                    report,
                    query_for_obligation,
                )
            )
            report = resolve_reference_retrieval_obligations(
                report,
                self.reference_resolver,
                query_for_obligation=query_for_obligation,
                limit=self.reference_limit,
            )
        else:
            reference_query_obligation_ids = self._reference_query_obligation_ids(tasks)

        if self.reference_resolver is None and (
            self.reference_catalog is not None and reference_query_obligation_ids
        ):
            report = resolve_reference_search_obligations(
                report,
                self.reference_catalog,
                query_for_obligation=self._query_for_obligation,
                reference_type=self.reference_type,
                limit=self.reference_limit,
                retrieval_method=self.retrieval_method,
            )

        resolved = replace(result, report=report, receipt=None)
        return CompResolutionResult(
            source=result,
            result=resolved,
            tasks=tasks,
            semantic_judgment_ids=tuple(
                judgment.judgment_id for judgment in semantic_judgments
            ),
            reference_query_obligation_ids=reference_query_obligation_ids,
        )

    def _semantic_judgments_for(
        self, tasks: tuple[ResolverTask, ...]
    ) -> tuple[SemanticJudgment, ...]:
        semantic_obligation_ids = {
            task.obligation_id
            for task in tasks
            if task.task_type == "semantic_judgment"
        }
        return tuple(
            judgment
            for judgment in self.semantic_judgments
            if judgment.obligation_id in semantic_obligation_ids
        )

    def _reference_query_obligation_ids(
        self, tasks: tuple[ResolverTask, ...]
    ) -> tuple[str, ...]:
        return tuple(
            task.obligation_id
            for task in tasks
            if task.task_type == "reference_search"
            and task.obligation_id in self.reference_queries
        )

    def _query_for_obligation(self, obligation: ProofObligation) -> str | None:
        task = resolver_task_from_obligation(obligation)
        return self.reference_queries.get(task.obligation_id)

    def _retrieval_query_for_obligation(self, tasks: tuple[ResolverTask, ...]):
        if self.reference_query_policy is not None:
            return reference_query_for_obligation_from_policy(
                tasks,
                policy=self.reference_query_policy,
                context=self.reference_query_context,
            )
        return reference_query_for_obligation_from_resolver_tasks(
            tasks,
            query_texts=self.reference_queries,
            lens=self.reference_lens,
            reference_type=self.reference_type,
        )

    def _retrieval_query_obligation_ids(
        self,
        report: CompileReport,
        query_for_obligation,
    ) -> tuple[str, ...]:
        return tuple(
            resolver_task_from_obligation(obligation).obligation_id
            for obligation in report.obligations
            if query_for_obligation(obligation) is not None
        )


__all__ = [
    "CompCompileResult",
    "CompResolutionResult",
    "CompCompilerAdapter",
    "DeterministicCompResolver",
]
