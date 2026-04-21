from comp.judgment import (
    CandidateSummary,
    CommitSpec,
    CompiledJudgmentProgram,
    DraftSnapshot,
    Fact,
    FixpointEngine,
    JudgmentState,
    ProjectionSpec,
    SubjectRef,
    TransferRule,
    committable,
    frontier,
    needs_review,
    winner_or_none,
)


def test_judgment_state_append_only_and_versions():
    subject = SubjectRef("claim", "c1")
    fact = Fact("proposed", subject, "amount", 100)

    state = JudgmentState()
    delta1 = state.add_facts([fact])
    delta2 = state.add_facts([fact])

    assert delta1 == {fact}
    assert delta2 == set()
    assert state.version_of(subject) == 1


def test_active_hazards_respect_discharge_facts():
    subject = SubjectRef("draft", "d1")
    state = JudgmentState()
    state.add_facts(
        [
            Fact("hazard_open", subject, "missing_unit", "obl-1"),
            Fact("hazard_open", subject, "needs_review", "obl-2"),
            Fact("hazard_discharge", subject, "missing_unit", "obl-1"),
        ]
    )

    assert state.active_hazard_ids(subject) == {"obl-2"}


def test_fixpoint_engine_chains_transfer_rules():
    subject = SubjectRef("claim", "c1")

    def emit_evidence(state, triggered):
        return {
            Fact("evidence", fact.subject, "support", fact.key, weight=1.0)
            for fact in triggered
        }

    def emit_provenance(state, triggered):
        return {
            Fact("prov_edge", fact.subject, "edge", f"{fact.subject.id}:{fact.key}")
            for fact in triggered
        }

    program = CompiledJudgmentProgram(
        transfers=(
            TransferRule(
                rule_id="proposed_to_evidence",
                subscribe_tags=("proposed",),
                match_kind="claim",
                emit=emit_evidence,
            ),
            TransferRule(
                rule_id="evidence_to_prov",
                subscribe_tags=("evidence",),
                match_kind="claim",
                emit=emit_provenance,
            ),
        )
    )

    engine = FixpointEngine(program)
    state = engine.run({Fact("proposed", subject, "amount", 100)})

    assert Fact("evidence", subject, "support", "amount", weight=1.0) in state.facts
    assert Fact("prov_edge", subject, "edge", "c1:support") in state.facts


def test_frontier_and_commit_helpers_work_together():
    summaries = [
        CandidateSummary("a", positive_evidence=3, specificity=2, provenance_depth=2),
        CandidateSummary("b", positive_evidence=1, specificity=1, provenance_depth=1),
        CandidateSummary("c", positive_evidence=3, specificity=2, provenance_depth=2),
    ]

    front = frontier(summaries)
    assert [item.candidate_id for item in front] == ["a", "c"]
    assert winner_or_none(summaries) is None
    assert needs_review(summaries) is True

    snapshot = DraftSnapshot(
        draft_id="draft-1",
        resolved_bundles=frozenset({"site", "amount"}),
        active_hazards=frozenset(),
        fresh=True,
        provenance_edges=2,
    )
    spec = CommitSpec(
        commit_id="row-commit",
        required_bundles=("site", "amount"),
        blocking_hazards=("missing_unit",),
        min_provenance_edges=1,
    )
    projection = ProjectionSpec("public-row", ("site", "amount"))

    assert committable(snapshot, spec) is True
    assert projection.output_fields == ("site", "amount")
