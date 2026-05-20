from __future__ import annotations

from collections.abc import Callable, Mapping

from comp.compiler_tool.models import ProofObligation
from comp.compiler_tool.resolver_tasks import ResolverTask, resolver_task_from_obligation
from comp.compiler_tool.retrieval import ReferenceQuery, RetrievalLens


def reference_query_from_resolver_task(
    task: ResolverTask,
    *,
    text: str,
    lens: RetrievalLens,
    reference_type: str | None = None,
) -> ReferenceQuery:
    if task.task_type != "reference_search":
        raise ValueError(
            "reference_query_from_resolver_task requires a reference_search task"
        )

    return ReferenceQuery(
        query_id=f"reference-query:{task.obligation_id}",
        text=text,
        lens=lens,
        reference_type=reference_type,
        source_artifact_ids=(task.task_id, task.obligation_id),
    )


def reference_query_for_obligation_from_resolver_tasks(
    tasks: tuple[ResolverTask, ...],
    *,
    query_texts: Mapping[str, str],
    lens: RetrievalLens,
    reference_type: str | None = None,
) -> Callable[[ProofObligation], ReferenceQuery | None]:
    queries_by_obligation_id = {
        task.obligation_id: reference_query_from_resolver_task(
            task,
            text=query_texts[task.obligation_id],
            lens=lens,
            reference_type=reference_type,
        )
        for task in tasks
        if task.task_type == "reference_search" and task.obligation_id in query_texts
    }

    def query_for_obligation(obligation: ProofObligation) -> ReferenceQuery | None:
        obligation_id = resolver_task_from_obligation(obligation).obligation_id
        return queries_by_obligation_id.get(obligation_id)

    return query_for_obligation


__all__ = [
    "reference_query_for_obligation_from_resolver_tasks",
    "reference_query_from_resolver_task",
]
