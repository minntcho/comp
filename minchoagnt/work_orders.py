from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any

from comp.compiler_tool import (
    ResolverTask,
    SemanticJudgment,
    apply_semantic_judgments,
    resolver_tasks_from_report,
)
from minchoagnt.comp_adapter import CompCompileResult


@dataclass(frozen=True)
class LLMWorkOrder:
    work_order_id: str
    target_id: str
    target_kind: str
    task_kind: str
    context_bundle: tuple[tuple[str, Any], ...] = field(default_factory=tuple)
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    forbidden_outputs: tuple[str, ...] = field(default_factory=tuple)
    expected_artifacts: tuple[str, ...] = field(default_factory=tuple)
    budget: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


@dataclass(frozen=True)
class LLMWorkerSubmission:
    work_order_id: str
    tool_name: str
    artifact: Any


@dataclass(frozen=True)
class AbstentionArtifact:
    abstention_id: str
    work_order_id: str
    reason: str
    category: str

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


@dataclass(frozen=True)
class LLMWorkerResult:
    work_order_id: str
    submissions: tuple[LLMWorkerSubmission, ...] = field(default_factory=tuple)
    abstention: AbstentionArtifact | None = None

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


class DeterministicLLMWorker:
    """Fixture LLM worker that submits typed artifacts without compiler authority."""

    def __init__(
        self,
        *,
        submissions: Iterable[LLMWorkerSubmission] = (),
        abstentions: Iterable[AbstentionArtifact] = (),
    ):
        self.submissions = tuple(submissions)
        self.abstentions = tuple(abstentions)

    def run(self, work_order: LLMWorkOrder) -> LLMWorkerResult:
        abstention = _matching_abstention(self.abstentions, work_order)
        if abstention is not None:
            return LLMWorkerResult(
                work_order_id=work_order.work_order_id,
                abstention=abstention,
            )

        submissions = tuple(
            submission
            for submission in self.submissions
            if submission.work_order_id == work_order.work_order_id
        )
        forbidden = _first_forbidden_submission(work_order, submissions)
        if forbidden is not None:
            return LLMWorkerResult(
                work_order_id=work_order.work_order_id,
                abstention=AbstentionArtifact(
                    abstention_id=(
                        f"abstain:{work_order.work_order_id}:forbidden_tool"
                    ),
                    work_order_id=work_order.work_order_id,
                    reason=(
                        f"Tool {forbidden.tool_name} is not allowed for this "
                        "work order."
                    ),
                    category="forbidden_tool",
                ),
            )

        return LLMWorkerResult(
            work_order_id=work_order.work_order_id,
            submissions=_limit_submissions(work_order, submissions),
        )


def semantic_work_orders_from_result(
    result: CompCompileResult,
) -> tuple[LLMWorkOrder, ...]:
    return semantic_work_orders_from_tasks(resolver_tasks_from_report(result.report))


def semantic_work_orders_from_tasks(
    tasks: tuple[ResolverTask, ...],
) -> tuple[LLMWorkOrder, ...]:
    return tuple(
        _semantic_work_order(task)
        for task in tasks
        if task.task_type == "semantic_judgment"
    )


def apply_llm_worker_results(
    result: CompCompileResult,
    worker_results: Iterable[LLMWorkerResult],
    *,
    available_span_ids: Iterable[str] | None = None,
) -> CompCompileResult:
    judgments = tuple(
        submission.artifact
        for worker_result in worker_results
        for submission in worker_result.submissions
        if (
            submission.tool_name == "submit_semantic_judgment"
            and isinstance(submission.artifact, SemanticJudgment)
        )
    )
    if not judgments:
        return replace(result, receipt=None)

    return replace(
        result,
        report=apply_semantic_judgments(
            result.report,
            judgments,
            available_span_ids=available_span_ids,
        ),
        receipt=None,
    )


def _semantic_work_order(task: ResolverTask) -> LLMWorkOrder:
    return LLMWorkOrder(
        work_order_id=f"llm-work-order:{task.obligation_id}",
        target_id=task.obligation_id,
        target_kind="proof_obligation",
        task_kind="semantic_judgment",
        context_bundle=task.payload,
        allowed_tools=(
            "submit_semantic_judgment",
            "flag_conflict",
            "abstain_with_reason",
        ),
        forbidden_outputs=(
            "create_reference_binding",
            "create_commit_receipt",
            "project_public_row",
        ),
        expected_artifacts=("semantic_judgment", "abstention"),
        budget=(("max_artifacts", 1),),
    )


def _matching_abstention(
    abstentions: tuple[AbstentionArtifact, ...],
    work_order: LLMWorkOrder,
) -> AbstentionArtifact | None:
    for abstention in abstentions:
        if abstention.work_order_id == work_order.work_order_id:
            return abstention
    return None


def _first_forbidden_submission(
    work_order: LLMWorkOrder,
    submissions: tuple[LLMWorkerSubmission, ...],
) -> LLMWorkerSubmission | None:
    allowed = set(work_order.allowed_tools)
    forbidden = set(work_order.forbidden_outputs)
    for submission in submissions:
        if submission.tool_name in forbidden or submission.tool_name not in allowed:
            return submission
    return None


def _limit_submissions(
    work_order: LLMWorkOrder,
    submissions: tuple[LLMWorkerSubmission, ...],
) -> tuple[LLMWorkerSubmission, ...]:
    budget = dict(work_order.budget)
    max_artifacts = budget.get("max_artifacts")
    if isinstance(max_artifacts, int):
        return submissions[:max_artifacts]
    return submissions


__all__ = [
    "LLMWorkOrder",
    "LLMWorkerSubmission",
    "LLMWorkerResult",
    "AbstentionArtifact",
    "DeterministicLLMWorker",
    "semantic_work_orders_from_result",
    "semantic_work_orders_from_tasks",
    "apply_llm_worker_results",
]
