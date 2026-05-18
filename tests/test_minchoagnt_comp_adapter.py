import pytest

import comp
from comp import ProjectionBlocked, ProjectionSpec, project_public_row
from comp.compiler_tool import (
    ClaimHypothesis,
    EvidenceWitness,
    InterpretationHypothesis,
)
from minchoagnt import MemoryStore, MiniAgent, ReviewWorkbench, SkillStore
from minchoagnt.comp_adapter import CompCompilerAdapter


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
    adapter = CompCompilerAdapter(allowed_units=frozenset({"kwh"}))
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-1",
        subject_id="claim-1",
        claims=(
            ClaimHypothesis("activity", "electricity", witness_id="w-activity"),
            ClaimHypothesis("amount", 1200, witness_id="w-amount"),
            ClaimHypothesis("unit", "kwh", witness_id="w-unit"),
        ),
        witnesses=(
            EvidenceWitness("w-activity", "activity", source="fragment-1"),
            EvidenceWitness("w-amount", "amount", source="fragment-1"),
            EvidenceWitness("w-unit", "unit", source="header-1"),
        ),
    )

    result = adapter.compile(hypothesis)

    assert result.subject.kind == "claim"
    assert result.subject.id == "hyp-1"
    assert result.report.status == "accepted"
    assert result.report.can_project_public_row is False

    projection = ProjectionSpec("public-row", ("activity", "amount", "unit"))
    with pytest.raises(ProjectionBlocked):
        project_public_row(
            {"activity": "electricity", "amount": 1200, "unit": "kwh"},
            projection,
        )


def test_comp_adapter_can_append_report_facts_without_minting_receipts():
    adapter = CompCompilerAdapter(allowed_units=frozenset({"kwh"}))
    hypothesis = InterpretationHypothesis(
        hypothesis_id="hyp-2",
        subject_id="claim-2",
        claims=(ClaimHypothesis("unit", "mwh", witness_id="w-unit"),),
        witnesses=(EvidenceWitness("w-unit", "unit", source="fragment-1"),),
    )

    result = adapter.compile(hypothesis)
    delta = adapter.record(result)

    assert result.report.status == "blocked"
    assert result.receipt is None
    assert any(fact.tag == "hazard_open" for fact in delta)
    assert result.judgment.active_hazard_ids(result.subject)
