import pytest

import comp
from comp import PublicOutputBlocked, PublicOutputSpec, build_public_output
from comp.compiler_tool import (
    CalculationRequirement,
    ClaimCandidate,
    ValidationReport,
    EvidenceRef,
    InterpretationHypothesis,
    ValidationRequirement,
    EmbeddingResolverStub,
    ReferenceCatalog,
    ReferenceIndexEntry,
    ReferenceRecord,
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    SemanticJudgment,
    SemanticJudgmentRequirement,
)
from comp.judgment import SubjectRef
from minchoagnt import (
    CompCompileResult,
    CompCompilerAdapter,
    DeterministicCompResolver,
    MemoryStore,
    MiniAgent,
    ReviewWorkbench,
    SkillStore,
)

TINY_KNOWN_FIELDS = frozenset({"activity", "amount", "unit", "reporting_year"})


def test_minchoagnt_layer_is_available_without_expanding_comp_surface():
    assert MiniAgent is not None
    assert MemoryStore is not None
    assert SkillStore is not None
    assert ReviewWorkbench is not None

    assert not hasattr(comp, "MiniAgent")
    assert not hasattr(comp, "MemoryStore")
    assert not hasattr(comp, "SkillStore")
    assert not hasattr(comp, "ReviewWorkbench")


def test_comp_adapter_calls_compiler_tool_without_projection_authority():
    adapter = CompCompilerAdapter(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    )
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-1",
        subject_id="claim-1",
        claims=(
            ClaimCandidate("activity", "electricity", witness_id="w-activity"),
            ClaimCandidate("amount", 1200, witness_id="w-amount"),
            ClaimCandidate("unit", "kwh", witness_id="w-unit"),
        ),
        witnesses=(
            EvidenceRef("w-activity", "activity", source="fragment-1"),
            EvidenceRef("w-amount", "amount", source="fragment-1"),
            EvidenceRef("w-unit", "unit", source="header-1"),
        ),
    )

    result = adapter.compile(hypothesis)

    assert result.subject.kind == "claim"
    assert result.subject.id == "hyp-1"
    assert result.report.status == "accepted"
    assert result.report.can_build_public_output is False

    projection = PublicOutputSpec("public-row", ("activity", "amount", "unit"))
    with pytest.raises(PublicOutputBlocked):
        build_public_output(
            {"activity": "electricity", "amount": 1200, "unit": "kwh"},
            projection,
        )


def test_comp_adapter_can_append_report_facts_without_minting_receipts():
    adapter = CompCompilerAdapter(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    )
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-2",
        subject_id="claim-2",
        claims=(ClaimCandidate("unit", "mwh", witness_id="w-unit"),),
        witnesses=(EvidenceRef("w-unit", "unit", source="fragment-1"),),
    )

    result = adapter.compile(hypothesis)
    delta = adapter.record(result)

    assert result.report.status == "blocked"
    assert result.receipt is None
    assert any(fact.tag == "hazard_open" for fact in delta)
    assert result.judgment.active_hazard_ids(result.subject)


def test_comp_adapter_exposes_resolver_tasks_for_agent_loop():
    adapter = CompCompilerAdapter(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    )
    result = adapter.compile(
        InterpretationHypothesis(
            hypothesis_id="hyp-3",
            subject_id="claim-3",
            claims=(ClaimCandidate("unit", "mwh", witness_id="w-unit"),),
            witnesses=(EvidenceRef("w-unit", "unit", source="fragment-1"),),
        )
    )

    tasks = adapter.resolver_tasks(result)

    assert len(tasks) == 1
    assert tasks[0].task_type == "evidence_search"
    assert tasks[0].required_artifact == "evidence_witness"
    assert tasks[0].requirement_kind == "find_source_witness"
    assert tasks[0].field == "unit"


def test_deterministic_comp_resolver_applies_semantic_judgment_without_receipt():
    obligation = ValidationRequirement(
        kind="semantic_judgment_required",
        field="scope2_method",
        reason="support_required",
        requirement_id="obl-scope2",
        semantic_requirement=SemanticJudgmentRequirement(
            question="Does this span support market-based Scope 2?",
            claim_id="claim-scope2",
            evidence_span_ids=("span-17",),
            rubric_id="ghg-protocol-scope2-method-v1",
            acceptable_verdicts=("supports", "refutes", "ambiguous"),
            allowed_judges=("llm/scope2-fixture",),
        ),
    )
    compile_result = CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-sem", "facility-1"),
        subject=SubjectRef("claim", "hyp-sem"),
        report=ValidationReport(status="review_required", validation_requirements=(obligation,)),
    )
    resolver = DeterministicCompResolver(
        semantic_judgments=(
            SemanticJudgment(
                judgment_id="judgment-scope2",
                requirement_id="obl-scope2",
                verdict="supports",
                rubric_id="ghg-protocol-scope2-method-v1",
                judge="llm/scope2-fixture",
                cited_span_ids=("span-17",),
                rationale="fixture judgment",
            ),
        ),
        available_span_ids=("span-17",),
    )

    resolution = resolver.resolve(compile_result)

    assert [task.requirement_id for task in resolution.tasks] == ["obl-scope2"]
    assert resolution.semantic_judgment_ids == ("judgment-scope2",)
    assert resolution.result.report.status == "accepted"
    assert resolution.result.report.validation_requirements == ()
    assert resolution.result.report.resolved_validation_requirements == (obligation,)
    assert resolution.result.receipt is None


def test_deterministic_comp_resolver_runs_reference_search_from_task_query():
    obligation_id = (
        "resolve:ghg.electricity_factor_multiplication.v1:"
        "hyp-1:co2e_emission:reference_search_required"
    )
    requirement = CalculationRequirement(
        reason="unknown_reference",
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_claim_id="hyp-1:co2e_emission",
        input_claim_id="hyp-1:amount",
        reference_binding_id="bind-amount-factor",
        reference_id="factor.missing",
    )
    obligation = ValidationRequirement(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        requirement_id=obligation_id,
        claim_id="hyp-1:co2e_emission",
        calculation_requirement=requirement,
    )
    compile_result = CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-ref", "facility-1"),
        subject=SubjectRef("claim", "hyp-ref"),
        report=ValidationReport(status="blocked", validation_requirements=(obligation,)),
    )
    catalog = ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                aliases=("korea electricity grid factor",),
            ),
        )
    )
    resolver = DeterministicCompResolver(
        reference_catalog=catalog,
        reference_queries={obligation_id: "korea electricity grid factor"},
        reference_type="emission_factor",
    )

    resolution = resolver.resolve(compile_result)

    assert resolution.reference_query_requirement_ids == (obligation_id,)
    reference_ids = [
        candidate.reference_id
        for candidate in resolution.result.report.reference_options
    ]
    assert reference_ids == ["factor.kr_grid.2024.location_based"]
    assert resolution.result.report.validation_requirements == ()
    assert resolution.result.report.resolved_validation_requirements == (obligation,)
    assert resolution.result.receipt is None


def test_deterministic_comp_resolver_runs_reference_retrieval_from_task_query():
    obligation_id = (
        "resolve:ghg.electricity_factor_multiplication.v1:"
        "hyp-1:co2e_emission:reference_search_required"
    )
    requirement = CalculationRequirement(
        reason="unknown_reference",
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_claim_id="hyp-1:co2e_emission",
        input_claim_id="hyp-1:amount",
        reference_binding_id="bind-amount-factor",
        reference_id="factor.missing",
    )
    obligation = ValidationRequirement(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        requirement_id=obligation_id,
        claim_id="hyp-1:co2e_emission",
        calculation_requirement=requirement,
    )
    compile_result = CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-ref", "facility-1"),
        subject=SubjectRef("claim", "hyp-ref"),
        report=ValidationReport(status="blocked", validation_requirements=(obligation,)),
    )
    resolver = DeterministicCompResolver(
        reference_resolver=EmbeddingResolverStub(
            entries=(
                ReferenceIndexEntry(
                    entry_id="idx-factor-kr-grid-2024",
                    reference_id="factor.kr_grid.2024.location_based",
                    reference_type="emission_factor",
                    lens="factor",
                    text="Korea grid electricity factor 2024 location based",
                    reference_db_version="refdb-v1",
                    index_version="embedding-stub-v1",
                ),
            )
        ),
        reference_queries={obligation_id: "Korea grid electricity factor 2024"},
        reference_lens="factor",
        reference_type="emission_factor",
    )

    resolution = resolver.resolve(compile_result)

    assert resolution.reference_query_requirement_ids == (obligation_id,)
    assert [
        candidate.retrieval_method
        for candidate in resolution.result.report.reference_options
    ] == ["embedding_stub:factor"]
    assert [
        candidate.reference_id
        for candidate in resolution.result.report.reference_options
    ] == ["factor.kr_grid.2024.location_based"]
    assert resolution.result.report.validation_requirements == ()
    assert resolution.result.report.resolved_validation_requirements == (obligation,)
    assert resolution.result.report.canonical_references == ()
    assert resolution.result.report.calculated_claims == ()
    assert resolution.result.receipt is None


def test_deterministic_comp_resolver_runs_reference_retrieval_from_query_policy():
    obligation_id = (
        "resolve:ghg.electricity_factor_multiplication.v1:"
        "hyp-1:co2e_emission:reference_search_required"
    )
    requirement = CalculationRequirement(
        reason="unknown_reference",
        formula_id="ghg.electricity_factor_multiplication.v1",
        output_claim_id="hyp-1:co2e_emission",
        input_claim_id="hyp-1:amount",
        reference_binding_id="bind-amount-factor",
        reference_id="factor.missing",
    )
    obligation = ValidationRequirement(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        requirement_id=obligation_id,
        claim_id="hyp-1:co2e_emission",
        calculation_requirement=requirement,
    )
    compile_result = CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-ref", "facility-1"),
        subject=SubjectRef("claim", "hyp-ref"),
        report=ValidationReport(status="blocked", validation_requirements=(obligation,)),
    )
    resolver = DeterministicCompResolver(
        reference_resolver=EmbeddingResolverStub(
            entries=(
                ReferenceIndexEntry(
                    entry_id="idx-factor-kr-grid-2024",
                    reference_id="factor.kr_grid.2024.location_based",
                    reference_type="emission_factor",
                    lens="factor",
                    text="Korea grid electricity factor 2024 location based",
                    reference_db_version="refdb-v1",
                    index_version="embedding-stub-v1",
                ),
            )
        ),
        reference_query_policy=RetrievalQueryPolicy(
            policy_id="ghg-reference-query-policy-v1",
            rules=(
                RetrievalQueryRule(
                    rule_id="electricity-factor-query-v1",
                    formula_id="ghg.electricity_factor_multiplication.v1",
                    lens="factor",
                    reference_type="emission_factor",
                    text_template=(
                        "{geography} grid electricity factor {reporting_year}"
                    ),
                ),
            ),
        ),
        reference_query_context={"geography": "Korea", "reporting_year": 2024},
    )

    resolution = resolver.resolve(compile_result)

    assert resolution.reference_query_requirement_ids == (obligation_id,)
    assert [
        candidate.reference_id
        for candidate in resolution.result.report.reference_options
    ] == ["factor.kr_grid.2024.location_based"]
    assert resolution.result.report.resolved_validation_requirements == (obligation,)
    assert resolution.result.report.canonical_references == ()
    assert resolution.result.report.calculated_claims == ()
    assert resolution.result.receipt is None


def test_deterministic_comp_resolver_leaves_reference_policy_task_open_without_context():
    obligation_id = (
        "resolve:ghg.electricity_factor_multiplication.v1:"
        "hyp-1:co2e_emission:reference_search_required"
    )
    obligation = ValidationRequirement(
        kind="reference_search_required",
        field="co2e_emission",
        reason="unknown_reference",
        requirement_id=obligation_id,
        claim_id="hyp-1:co2e_emission",
        calculation_requirement=CalculationRequirement(
            reason="unknown_reference",
            formula_id="ghg.electricity_factor_multiplication.v1",
            output_claim_id="hyp-1:co2e_emission",
        ),
    )
    compile_result = CompCompileResult(
        hypothesis=InterpretationHypothesis("hyp-ref", "facility-1"),
        subject=SubjectRef("claim", "hyp-ref"),
        report=ValidationReport(status="blocked", validation_requirements=(obligation,)),
    )
    resolver = DeterministicCompResolver(
        reference_resolver=EmbeddingResolverStub(entries=()),
        reference_query_policy=RetrievalQueryPolicy(
            policy_id="ghg-reference-query-policy-v1",
            rules=(
                RetrievalQueryRule(
                    rule_id="electricity-factor-query-v1",
                    formula_id="ghg.electricity_factor_multiplication.v1",
                    lens="factor",
                    reference_type="emission_factor",
                    text_template=(
                        "{geography} grid electricity factor {reporting_year}"
                    ),
                ),
            ),
        ),
        reference_query_context={"geography": "Korea"},
    )

    resolution = resolver.resolve(compile_result)

    assert resolution.reference_query_requirement_ids == ()
    assert resolution.result.report == compile_result.report
    assert resolution.result.receipt is None
