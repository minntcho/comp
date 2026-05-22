from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from comp.compiler_tool import (
    ClaimCandidate,
    EvidenceRef,
    InterpretationHypothesis,
    ValidationReport,
    resolver_tasks_from_report,
)
from minchoagnt.comp_adapter import CompCompileResult, CompCompilerAdapter


RevisionStopReason = Literal["accepted", "max_revisions", "no_revision"]


@dataclass(frozen=True)
class WitnessFixtureRule:
    field: str
    witness_id: str
    source: str | None
    span: str | None = None
    text: str | None = None

    @property
    def rule_id(self) -> str:
        return f"witness_fixture:{self.field}:{self.witness_id}"


@dataclass(frozen=True)
class WitnessRequest:
    requirement_id: str
    field: str
    reason: str


@dataclass(frozen=True)
class ObligationReflection:
    status: str
    witness_requests: tuple[WitnessRequest, ...] = field(default_factory=tuple)
    unhandled_requirement_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RevisionWorkItem:
    work_item_id: str
    requirement_id: str
    task_kind: str
    field: str
    reason: str
    allowed_actions: tuple[str, ...] = field(default_factory=tuple)
    forbidden_outputs: tuple[str, ...] = field(default_factory=tuple)
    expected_artifacts: tuple[str, ...] = field(default_factory=tuple)

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


@dataclass(frozen=True)
class RevisionWorkerSubmission:
    work_item_id: str
    action: str
    artifact: Any


@dataclass(frozen=True)
class RevisionAbstention:
    abstention_id: str
    work_item_id: str
    reason: str
    category: str

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


@dataclass(frozen=True)
class RevisionWorkerResult:
    work_item_id: str
    submissions: tuple[RevisionWorkerSubmission, ...] = field(default_factory=tuple)
    abstention: RevisionAbstention | None = None

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


class DeterministicRevisionWorker:
    def __init__(
        self,
        *,
        submissions: Iterable[RevisionWorkerSubmission] = (),
        abstentions: Iterable[RevisionAbstention] = (),
    ):
        self.submissions = tuple(submissions)
        self.abstentions = tuple(abstentions)

    def run(self, work_item: RevisionWorkItem) -> RevisionWorkerResult:
        for abstention in self.abstentions:
            if abstention.work_item_id == work_item.work_item_id:
                return RevisionWorkerResult(
                    work_item_id=work_item.work_item_id,
                    abstention=abstention,
                )

        submissions = tuple(
            submission
            for submission in self.submissions
            if submission.work_item_id == work_item.work_item_id
        )
        for submission in submissions:
            if (
                submission.action in work_item.forbidden_outputs
                or submission.action not in work_item.allowed_actions
            ):
                return RevisionWorkerResult(
                    work_item_id=work_item.work_item_id,
                    abstention=RevisionAbstention(
                        abstention_id=(
                            f"abstain:{work_item.work_item_id}:forbidden_action"
                        ),
                        work_item_id=work_item.work_item_id,
                        reason=(
                            f"Action {submission.action} is not allowed for this "
                            "revision work item."
                        ),
                        category="forbidden_action",
                    ),
                )

        return RevisionWorkerResult(
            work_item_id=work_item.work_item_id,
            submissions=submissions,
        )


@dataclass(frozen=True)
class RevisedHypothesis:
    source_hypothesis_id: str
    hypothesis: InterpretationHypothesis
    applied_requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    unapplied_requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    applied_rule_ids: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class RevisionIteration:
    revision_index: int
    source: CompCompileResult
    reflection: ObligationReflection
    revision: RevisedHypothesis
    result: CompCompileResult


@dataclass(frozen=True)
class LoopTrace:
    initial: CompCompileResult
    iterations: tuple[RevisionIteration, ...] = field(default_factory=tuple)
    stop_reason: RevisionStopReason = "accepted"
    receipt: None = None

    @property
    def final(self) -> CompCompileResult:
        if not self.iterations:
            return self.initial
        return self.iterations[-1].result


def obligation_reflection(report: ValidationReport) -> ObligationReflection:
    witness_requests: list[WitnessRequest] = []
    unhandled_requirement_ids: list[str] = []

    for task in resolver_tasks_from_report(report):
        if (
            task.requirement_kind == "find_source_witness"
            and task.reason == "missing_source_witness"
        ):
            witness_requests.append(
                WitnessRequest(
                    requirement_id=task.requirement_id,
                    field=task.field,
                    reason=task.reason,
                )
            )
            continue
        unhandled_requirement_ids.append(task.requirement_id)

    return ObligationReflection(
        status=report.status,
        witness_requests=tuple(witness_requests),
        unhandled_requirement_ids=tuple(unhandled_requirement_ids),
    )


def revision_work_items_from_reflection(
    reflection: ObligationReflection,
) -> tuple[RevisionWorkItem, ...]:
    return tuple(
        RevisionWorkItem(
            work_item_id=f"revision-work-item:{request.requirement_id}",
            requirement_id=request.requirement_id,
            task_kind="attach_source_witness",
            field=request.field,
            reason=request.reason,
            allowed_actions=(
                "attach_grounded_witness",
                "abstain_with_reason",
            ),
            forbidden_outputs=(
                "create_reference_binding",
                "create_commit_receipt",
                "build_public_output",
            ),
            expected_artifacts=("evidence_witness", "abstention"),
        )
        for request in reflection.witness_requests
    )


def fixture_rules_from_revision_worker_results(
    worker_results: Iterable[RevisionWorkerResult],
) -> tuple[WitnessFixtureRule, ...]:
    return tuple(
        submission.artifact
        for worker_result in worker_results
        for submission in worker_result.submissions
        if (
            submission.action == "attach_grounded_witness"
            and isinstance(submission.artifact, WitnessFixtureRule)
        )
    )


def revised_hypothesis_fixture(
    hypothesis: InterpretationHypothesis,
    reflection: ObligationReflection,
    *,
    fixture_rules: tuple[WitnessFixtureRule, ...] = (),
) -> RevisedHypothesis:
    rules_by_field = {rule.field: rule for rule in fixture_rules}
    applied_requests: list[WitnessRequest] = []
    applied_rules: list[WitnessFixtureRule] = []
    unapplied_requirement_ids: list[str] = list(reflection.unhandled_requirement_ids)

    for request in reflection.witness_requests:
        rule = rules_by_field.get(request.field)
        if rule is None:
            unapplied_requirement_ids.append(request.requirement_id)
            continue
        applied_requests.append(request)
        applied_rules.append(rule)

    if not applied_requests:
        return RevisedHypothesis(
            source_hypothesis_id=hypothesis.hypothesis_id,
            hypothesis=hypothesis,
            unapplied_requirement_ids=tuple(unapplied_requirement_ids),
        )

    witness_ids = {witness.witness_id for witness in hypothesis.witnesses}
    new_witnesses = list(hypothesis.witnesses)
    for rule in applied_rules:
        if rule.witness_id not in witness_ids:
            new_witnesses.append(
                EvidenceRef(
                    witness_id=rule.witness_id,
                    field=rule.field,
                    source=rule.source,
                    span=rule.span,
                    text=rule.text,
                )
            )
            witness_ids.add(rule.witness_id)

    witness_id_by_field = {rule.field: rule.witness_id for rule in applied_rules}
    revised_claims = tuple(
        _revise_claim_witness(claim, witness_id_by_field)
        for claim in hypothesis.claims
    )

    return RevisedHypothesis(
        source_hypothesis_id=hypothesis.hypothesis_id,
        hypothesis=InterpretationHypothesis(
            hypothesis_id=f"{hypothesis.hypothesis_id}:revision",
            subject_id=hypothesis.subject_id,
            claims=revised_claims,
            witnesses=tuple(new_witnesses),
        ),
        applied_requirement_ids=tuple(
            request.requirement_id for request in applied_requests
        ),
        unapplied_requirement_ids=tuple(unapplied_requirement_ids),
        applied_rule_ids=tuple(rule.rule_id for rule in applied_rules),
    )


def deterministic_revision_loop(
    adapter: CompCompilerAdapter,
    hypothesis: InterpretationHypothesis,
    *,
    fixture_rules: tuple[WitnessFixtureRule, ...] = (),
    max_revisions: int = 1,
) -> LoopTrace:
    if max_revisions < 0:
        raise ValueError("max_revisions must be non-negative.")

    initial = adapter.compile(hypothesis)
    current = initial
    iterations: list[RevisionIteration] = []
    stop_reason: RevisionStopReason = "accepted"

    for revision_index in range(1, max_revisions + 1):
        if current.report.status == "accepted":
            stop_reason = "accepted"
            break

        reflection = obligation_reflection(current.report)
        revision = revised_hypothesis_fixture(
            current.hypothesis,
            reflection,
            fixture_rules=fixture_rules,
        )
        if not revision.applied_requirement_ids:
            stop_reason = "no_revision"
            break

        revised = adapter.compile(revision.hypothesis)
        iteration = RevisionIteration(
            revision_index=revision_index,
            source=current,
            reflection=reflection,
            revision=revision,
            result=revised,
        )
        iterations.append(iteration)
        current = revised
        if current.report.status == "accepted":
            stop_reason = "accepted"
            break
        stop_reason = "max_revisions"

    if max_revisions == 0 and current.report.status != "accepted":
        stop_reason = "max_revisions"

    return LoopTrace(
        initial=initial,
        iterations=tuple(iterations),
        stop_reason=stop_reason,
        receipt=None,
    )


def _revise_claim_witness(
    claim: ClaimCandidate,
    witness_id_by_field: dict[str, str],
) -> ClaimCandidate:
    witness_id = witness_id_by_field.get(claim.field)
    if witness_id is None:
        return claim
    return replace(claim, witness_id=witness_id)


__all__ = [
    "DeterministicRevisionWorker",
    "LoopTrace",
    "ObligationReflection",
    "RevisionAbstention",
    "RevisedHypothesis",
    "RevisionStopReason",
    "RevisionIteration",
    "RevisionWorkItem",
    "RevisionWorkerResult",
    "RevisionWorkerSubmission",
    "WitnessFixtureRule",
    "WitnessRequest",
    "deterministic_revision_loop",
    "fixture_rules_from_revision_worker_results",
    "obligation_reflection",
    "revision_work_items_from_reflection",
    "revised_hypothesis_fixture",
]
