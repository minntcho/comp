from comp.compiler_tool import (
    CalculationRequirement,
    ValidationReport,
    ValidationRequirement,
    ResolverTask,
    SemanticJudgmentRequirement,
    resolver_tasks_from_report,
)


def test_semantic_obligation_becomes_resolver_task_with_rubric_payload():
    report = ValidationReport(
        status="review_required",
        obligations=(
            ValidationRequirement(
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
                    allowed_judges=("llm/scope2-fixture",),
                ),
            ),
        ),
    )

    tasks = resolver_tasks_from_report(report)

    assert tasks == (
        ResolverTask(
            task_id="resolver-task:obl-scope2",
            obligation_id="obl-scope2",
            task_type="semantic_judgment",
            required_artifact="semantic_judgment",
            obligation_kind="semantic_judgment_required",
            field="scope2_method",
            reason="support_required",
            claim_id="claim-scope2",
            blocking=True,
            payload=(
                ("question", "Does this span support market-based Scope 2?"),
                ("rubric_id", "ghg-protocol-scope2-method-v1"),
                ("acceptable_verdicts", ("supports", "refutes", "ambiguous")),
                ("required_verdict", "supports"),
                ("allowed_judges", ("llm/scope2-fixture",)),
                ("evidence_span_ids", ("span-17",)),
            ),
        ),
    )


def test_calculation_reference_search_obligation_preserves_requirement_payload():
    requirement = CalculationRequirement(
        reason="unknown_reference",
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_claim_id="hyp-1:co2e_emission",
        input_claim_id="hyp-1:amount",
        reference_binding_id="bind-amount-factor",
        reference_id="factor.kr_grid.2024.location_based",
    )
    report = ValidationReport(
        status="blocked",
        obligations=(
            ValidationRequirement(
                kind="reference_search_required",
                field="co2e_emission",
                reason="unknown_reference",
                obligation_id="resolve:ghg.electricity_factor_multiplication.v1:"
                "hyp-1:co2e_emission:reference_search_required",
                claim_id="hyp-1:co2e_emission",
                calculation_requirement=requirement,
            ),
        ),
    )

    task = resolver_tasks_from_report(report)[0]

    assert task.task_type == "reference_search"
    assert task.required_artifact == "reference_candidates"
    assert task.obligation_id == (
        "resolve:ghg.electricity_factor_multiplication.v1:"
        "hyp-1:co2e_emission:reference_search_required"
    )
    assert task.payload == (
        ("calculation_reason", "unknown_reference"),
        ("formula_id", "ghg.electricity_factor_multiplication.v1"),
        ("output_claim_id", "hyp-1:co2e_emission"),
        ("input_claim_id", "hyp-1:amount"),
        ("reference_binding_id", "bind-amount-factor"),
        ("reference_id", "factor.kr_grid.2024.location_based"),
    )


def test_resolver_tasks_use_fallback_obligation_ids_and_ignore_resolved_items():
    report = ValidationReport(
        status="review_required",
        obligations=(
            ValidationRequirement(
                kind="find_source_witness",
                field="unit",
                reason="missing_unit",
                blocking=True,
            ),
        ),
        resolved_obligations=(
            ValidationRequirement(
                kind="find_source_witness",
                field="amount",
                reason="missing_amount",
            ),
        ),
    )

    tasks = resolver_tasks_from_report(report)

    assert tasks == (
        ResolverTask(
            task_id="resolver-task:proof_obligation:find_source_witness:unit:"
            "missing_unit",
            obligation_id="proof_obligation:find_source_witness:unit:missing_unit",
            task_type="evidence_search",
            required_artifact="evidence_witness",
            obligation_kind="find_source_witness",
            field="unit",
            reason="missing_unit",
            claim_id=None,
            blocking=True,
            payload=(),
        ),
    )
