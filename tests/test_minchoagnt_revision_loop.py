from comp.compiler_tool import (
    ClaimCandidate,
    EvidenceRef,
    InterpretationHypothesis,
)
from minchoagnt import (
    CompCompilerAdapter,
    LoopTrace,
    ObligationReflection,
    RevisedHypothesis,
    RevisionIteration,
    RevisionWorkItem,
    WitnessFixtureRule,
    WitnessRequest,
    deterministic_revision_loop,
    obligation_reflection,
    revision_work_items_from_reflection,
    revised_hypothesis_fixture,
)


TINY_KNOWN_FIELDS = frozenset({"activity", "amount", "unit", "reporting_year"})


def test_obligation_reflection_extracts_missing_source_witness_request():
    adapter = _adapter()
    result = adapter.compile(_missing_unit_witness_hypothesis())

    reflection = obligation_reflection(result.report)

    assert reflection == ObligationReflection(
        status="blocked",
        witness_requests=(
            WitnessRequest(
                requirement_id=(
                    "validation_requirement:find_source_witness:"
                    "unit:missing_source_witness"
                ),
                field="unit",
                reason="missing_source_witness",
            ),
        ),
        unhandled_requirement_ids=(),
    )


def test_missing_source_witness_reflection_becomes_revision_work_item():
    result = _adapter().compile(_missing_unit_witness_hypothesis())
    reflection = obligation_reflection(result.report)

    work_items = revision_work_items_from_reflection(reflection)

    assert work_items == (
        RevisionWorkItem(
            work_item_id=(
                "revision-work-item:"
                "validation_requirement:find_source_witness:"
                "unit:missing_source_witness"
            ),
            requirement_id=(
                "validation_requirement:find_source_witness:"
                "unit:missing_source_witness"
            ),
            task_kind="attach_source_witness",
            field="unit",
            reason="missing_source_witness",
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
        ),
    )
    assert work_items[0].can_authorize_public_projection is False


def test_revised_hypothesis_fixture_adds_grounded_witness_without_mutating_source():
    hypothesis = _missing_unit_witness_hypothesis()
    reflection = obligation_reflection(_adapter().compile(hypothesis).report)
    rule = WitnessFixtureRule(
        field="unit",
        witness_id="w-unit",
        source="invoice.csv",
        span="unit-column",
        text="Unit: kWh",
    )

    revision = revised_hypothesis_fixture(
        hypothesis,
        reflection,
        fixture_rules=(rule,),
    )

    assert revision == RevisedHypothesis(
        source_hypothesis_id="hyp-rev-1",
        hypothesis=InterpretationHypothesis(
            hypothesis_id="hyp-rev-1:revision",
            subject_id="claim-1",
            claims=(
                ClaimCandidate("unit", "kwh", witness_id="w-unit"),
            ),
            witnesses=(
                EvidenceRef(
                    "w-unit",
                    "unit",
                    source="invoice.csv",
                    span="unit-column",
                    text="Unit: kWh",
                ),
            ),
        ),
        applied_requirement_ids=(
            "validation_requirement:find_source_witness:unit:missing_source_witness",
        ),
        applied_rule_ids=("witness_fixture:unit:w-unit",),
    )
    assert hypothesis.claims[0].witness_id is None
    assert hypothesis.witnesses == ()


def test_deterministic_revision_loop_recompiles_revised_hypothesis():
    trace = deterministic_revision_loop(
        _adapter(),
        _missing_unit_witness_hypothesis(),
        fixture_rules=(
            WitnessFixtureRule(
                field="unit",
                witness_id="w-unit",
                source="invoice.csv",
            ),
        ),
        max_revisions=1,
    )

    assert trace.initial.report.status == "blocked"
    assert len(trace.iterations) == 1
    revised_claim = trace.iterations[0].revision.hypothesis.claims[0]
    assert revised_claim.witness_id == "w-unit"
    assert trace.iterations[0].result.report.status == "accepted"
    assert trace.final.report.status == "accepted"
    assert trace.stop_reason == "accepted"


def test_revision_loop_never_mints_receipts_after_accepted_report():
    trace = deterministic_revision_loop(
        _adapter(),
        _missing_unit_witness_hypothesis(),
        fixture_rules=(
            WitnessFixtureRule(
                field="unit",
                witness_id="w-unit",
                source="invoice.csv",
            ),
        ),
        max_revisions=2,
    )

    assert isinstance(trace, LoopTrace)
    assert isinstance(trace.iterations[0], RevisionIteration)
    assert trace.initial.receipt is None
    assert trace.receipt is None
    assert trace.final.receipt is None
    assert all(iteration.result.receipt is None for iteration in trace.iterations)


def test_unsupported_unit_reflection_stays_unhandled():
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-unsupported-unit",
        subject_id="claim-1",
        claims=(ClaimCandidate("unit", "mwh", witness_id="w-unit"),),
        witnesses=(EvidenceRef("w-unit", "unit", source="invoice.csv"),),
    )
    result = _adapter().compile(hypothesis)

    reflection = obligation_reflection(result.report)
    revision = revised_hypothesis_fixture(
        hypothesis,
        reflection,
        fixture_rules=(
            WitnessFixtureRule(
                field="unit",
                witness_id="w-unit-2",
                source="invoice.csv",
            ),
        ),
    )

    assert reflection.witness_requests == ()
    assert reflection.unhandled_requirement_ids == (
        "validation_requirement:find_source_witness:unit:unsupported_unit",
    )
    assert revision_work_items_from_reflection(reflection) == ()
    assert revision.hypothesis == hypothesis
    assert revision.applied_requirement_ids == ()


def test_unapplied_witness_request_is_visible_in_revision_trace():
    result = _adapter().compile(_missing_unit_witness_hypothesis())
    reflection = obligation_reflection(result.report)

    revision = revised_hypothesis_fixture(
        result.hypothesis,
        reflection,
        fixture_rules=(),
    )

    assert revision.hypothesis == result.hypothesis
    assert revision.applied_requirement_ids == ()
    assert revision.unapplied_requirement_ids == (
        "validation_requirement:find_source_witness:unit:missing_source_witness",
    )


def test_revision_loop_records_no_revision_stop_reason():
    trace = deterministic_revision_loop(
        _adapter(),
        _missing_unit_witness_hypothesis(),
        fixture_rules=(),
        max_revisions=2,
    )

    assert trace.iterations == ()
    assert trace.stop_reason == "no_revision"
    assert trace.final.report.status == "blocked"


def test_revision_loop_records_max_revisions_stop_reason():
    trace = deterministic_revision_loop(
        _adapter(),
        _missing_unit_witness_hypothesis(),
        fixture_rules=(
            WitnessFixtureRule(
                field="unit",
                witness_id="w-unit",
                source=None,
            ),
        ),
        max_revisions=1,
    )

    assert len(trace.iterations) == 1
    assert trace.iterations[0].result.report.status == "blocked"
    assert trace.stop_reason == "max_revisions"


def test_revision_loop_records_initial_accepted_stop_reason():
    accepted = InterpretationHypothesis(
        hypothesis_id="hyp-accepted",
        subject_id="claim-1",
        claims=(ClaimCandidate("unit", "kwh", witness_id="w-unit"),),
        witnesses=(EvidenceRef("w-unit", "unit", source="invoice.csv"),),
    )

    trace = deterministic_revision_loop(
        _adapter(),
        accepted,
        fixture_rules=(),
        max_revisions=2,
    )

    assert trace.initial.report.status == "accepted"
    assert trace.iterations == ()
    assert trace.stop_reason == "accepted"


def _adapter():
    return CompCompilerAdapter(
        allowed_units=frozenset({"kwh"}),
        known_fields=TINY_KNOWN_FIELDS,
    )


def _missing_unit_witness_hypothesis():
    return InterpretationHypothesis(
        hypothesis_id="hyp-rev-1",
        subject_id="claim-1",
        claims=(ClaimCandidate("unit", "kwh", witness_id=None),),
        witnesses=(),
    )
