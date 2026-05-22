from comp.compiler_tool import (
    ValidationReport,
    InterpretationHypothesis,
    ValidationRequirement,
    SemanticJudgment,
    SemanticJudgmentRequirement,
)
from comp.judgment import SubjectRef
from minchoagnt import (
    AbstentionArtifact,
    CompCompileResult,
    DeterministicLLMWorker,
    LLMWorkOrder,
    LLMWorkerSubmission,
    apply_llm_worker_results,
    semantic_work_orders_from_result,
)


def _semantic_obligation() -> ValidationRequirement:
    return ValidationRequirement(
        kind="semantic_judgment_required",
        field="scope2_method",
        reason="support_required",
        obligation_id="obl-scope2",
        claim_id="claim-scope2",
        semantic_requirement=SemanticJudgmentRequirement(
            question="Does this span support market-based Scope 2?",
            claim_id="claim-scope2",
            evidence_span_ids=("span-17",),
            rubric_id="ghg-protocol-scope2-method-v1",
            acceptable_verdicts=("supports", "refutes", "ambiguous"),
            required_verdict="supports",
            allowed_judges=("llm/scope2-worker",),
        ),
    )


def _compile_result() -> CompCompileResult:
    return CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-sem", "facility-1"),
        subject=SubjectRef("claim", "hyp-sem"),
        report=ValidationReport(
            status="review_required",
            obligations=(_semantic_obligation(),),
        ),
    )


def _judgment() -> SemanticJudgment:
    return SemanticJudgment(
        judgment_id="judgment-scope2",
        obligation_id="obl-scope2",
        verdict="supports",
        rubric_id="ghg-protocol-scope2-method-v1",
        judge="llm/scope2-worker",
        cited_span_ids=("span-17",),
        rationale="The cited span states a market-based Scope 2 method.",
    )


def test_semantic_resolver_task_becomes_llm_work_order_with_limited_tools():
    result = _compile_result()

    work_orders = semantic_work_orders_from_result(result)

    assert work_orders == (
        LLMWorkOrder(
            work_order_id="llm-work-order:obl-scope2",
            target_id="obl-scope2",
            target_kind="proof_obligation",
            task_kind="semantic_judgment",
            context_bundle=(
                ("question", "Does this span support market-based Scope 2?"),
                ("rubric_id", "ghg-protocol-scope2-method-v1"),
                ("acceptable_verdicts", ("supports", "refutes", "ambiguous")),
                ("required_verdict", "supports"),
                ("allowed_judges", ("llm/scope2-worker",)),
                ("evidence_span_ids", ("span-17",)),
            ),
            allowed_tools=(
                "submit_semantic_judgment",
                "flag_conflict",
                "abstain_with_reason",
            ),
            forbidden_outputs=(
                "create_reference_binding",
                "create_commit_receipt",
                "build_public_output",
            ),
            expected_artifacts=("semantic_judgment", "abstention"),
            budget=(("max_artifacts", 1),),
        ),
    )
    assert work_orders[0].can_authorize_public_projection is False


def test_deterministic_llm_worker_submits_semantic_judgment_artifact_only():
    result = _compile_result()
    worker = DeterministicLLMWorker(
        submissions=(
            LLMWorkerSubmission(
                work_order_id="llm-work-order:obl-scope2",
                tool_name="submit_semantic_judgment",
                artifact=_judgment(),
            ),
        ),
    )

    worker_results = tuple(
        worker.run(order) for order in semantic_work_orders_from_result(result)
    )
    resolved = apply_llm_worker_results(
        result,
        worker_results,
        available_span_ids=("span-17",),
    )

    assert resolved.report.status == "accepted"
    assert resolved.report.obligations == ()
    assert resolved.report.resolved_obligations == (_semantic_obligation(),)
    assert resolved.receipt is None


def test_llm_worker_abstention_leaves_semantic_obligation_open():
    result = _compile_result()
    worker = DeterministicLLMWorker(
        abstentions=(
            AbstentionArtifact(
                abstention_id="abstain-scope2",
                work_order_id="llm-work-order:obl-scope2",
                reason="The provided span is not enough to judge the method.",
                category="cannot_resolve_from_available_context",
            ),
        ),
    )

    worker_results = tuple(
        worker.run(order) for order in semantic_work_orders_from_result(result)
    )
    unresolved = apply_llm_worker_results(
        result,
        worker_results,
        available_span_ids=("span-17",),
    )

    assert unresolved.report.status == "review_required"
    assert unresolved.report.obligations == (_semantic_obligation(),)
    assert unresolved.report.resolved_obligations == ()
    assert unresolved.receipt is None


def test_deterministic_llm_worker_rejects_forbidden_tool_submission():
    order = semantic_work_orders_from_result(_compile_result())[0]
    worker = DeterministicLLMWorker(
        submissions=(
            LLMWorkerSubmission(
                work_order_id=order.work_order_id,
                tool_name="create_commit_receipt",
                artifact={"receipt": "fake"},
            ),
        ),
    )

    result = worker.run(order)

    assert result.submissions == ()
    assert result.abstention == AbstentionArtifact(
        abstention_id="abstain:llm-work-order:obl-scope2:forbidden_tool",
        work_order_id="llm-work-order:obl-scope2",
        reason="Tool create_commit_receipt is not allowed for this work order.",
        category="forbidden_tool",
    )
