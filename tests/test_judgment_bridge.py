from types import SimpleNamespace

from artifacts import CanonicalRowArtifact, ClaimArtifact, CompileArtifacts, PartialFrameArtifact, RoleSlotArtifact
from compiled_spec import CompiledGovernancePolicy, CompiledProgramSpec, CompiledResolverPolicy
from governance_pass import GovernancePass
from repair_pass import RepairPass
from rule_ir import RuleLiteral
from spec_nodes import GovernancePolicy, ProgramSpec, ResolverPolicy


def test_repair_pass_records_selection_receipts():
    frame = PartialFrameArtifact(
        frame_id="frame-1",
        parser_name="parser-a",
        frame_type="ActivityFrame",
        slots={
            "raw_amount": RoleSlotArtifact(
                role_name="raw_amount",
                active_claim_id="claim-1",
                shadow_claim_ids=["claim-2"],
            )
        },
    )
    claims = [
        ClaimArtifact(
            claim_id="claim-1",
            frame_id="frame-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="raw_amount",
            value=100.0,
            confidence=0.8,
            extraction_mode="explicit",
            candidate_state="active",
        ),
        ClaimArtifact(
            claim_id="claim-2",
            frame_id="frame-1",
            fragment_id="frag-1",
            parser_name="parser-a",
            role_name="raw_amount",
            value=95.0,
            confidence=0.4,
            extraction_mode="derived",
            candidate_state="shadow",
        ),
    ]
    artifacts = CompileArtifacts(claims=claims, frames=[frame])
    spec = CompiledProgramSpec(
        syntax=ProgramSpec(module_name="m"),
        compiled_resolvers={
            "ActivityFrame": CompiledResolverPolicy(
                syntax=ResolverPolicy(frame_name="ActivityFrame")
            )
        },
    )
    env = SimpleNamespace(policy_flags={})

    RepairPass().run(spec, artifacts, env)

    receipts = frame.metadata.get("selection_receipts")
    assert isinstance(receipts, list)
    assert len(receipts) == 1
    assert receipts[0]["bundle_id"] == "frame-1:raw_amount"
    assert receipts[0]["winner_id"] == "claim-1"


def test_governance_pass_records_commit_receipt_on_merge():
    row = CanonicalRowArtifact(
        row_id="row-1",
        frame_id="frame-1",
        parser_name="parser-a",
        frame_type="ActivityFrame",
        status="committed",
        site_id="site-1",
        period="2025-03",
        activity_type="electricity",
        raw_amount=100.0,
        raw_unit="kwh",
        source_fragment_ids=["frag-1"],
    )
    artifacts = CompileArtifacts(rows=[row])
    spec = CompiledProgramSpec(
        syntax=ProgramSpec(module_name="m"),
        compiled_governances={
            "ActivityFrame": CompiledGovernancePolicy(
                syntax=GovernancePolicy(frame_name="ActivityFrame"),
                merge_conditions_ir=[RuleLiteral(True)],
            )
        },
    )
    env = SimpleNamespace(policy_flags={})

    GovernancePass().run(spec, artifacts, env)

    assert row.status == "merged"
    assert len(artifacts.commit_log) == 1
    assert row.metadata["commit_receipt"]["public_row_id"] == "row-1"
    assert artifacts.merge_log[0].action == "merge"


def test_governance_pass_uses_commit_barrier_for_error_rows():
    row = CanonicalRowArtifact(
        row_id="row-2",
        frame_id="frame-2",
        parser_name="parser-a",
        frame_type="ActivityFrame",
        status="committed",
        site_id="site-1",
        error_codes=["UnitActivityMismatch"],
    )
    artifacts = CompileArtifacts(rows=[row])
    spec = CompiledProgramSpec(
        syntax=ProgramSpec(module_name="m"),
        compiled_governances={
            "ActivityFrame": CompiledGovernancePolicy(
                syntax=GovernancePolicy(frame_name="ActivityFrame"),
                merge_conditions_ir=[RuleLiteral(True)],
            )
        },
    )
    env = SimpleNamespace(policy_flags={})

    GovernancePass().run(spec, artifacts, env)

    assert row.status == "committed"
    assert artifacts.commit_log == []
    assert artifacts.merge_log[0].action == "hold"
    assert "commit_blocked_by_hazard" in artifacts.merge_log[0].reason_codes
