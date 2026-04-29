import pytest

from artifacts import (
    CanonicalRowArtifact,
    ClaimArtifact,
    PartialFrameArtifact,
    RoleSlotArtifact,
)
from ast_nodes import BinaryExpr, FunctionCallExpr, LiteralExpr, NameExpr
from binder import BindingError
from compiled_spec import CompiledProgramSpec
from governance_pass import GovernancePass
from pipeline_runner import ESGPipelineRunner, compile_program_spec
from repair_pass import RepairPass
from spec_nodes import FieldSpec, FrameSpec, GovernancePolicy, ProgramSpec, ResolverPolicy


class SeedFramePass:
    def run(self, spec, artifacts, env):
        claim = ClaimArtifact(
            claim_id="CLM-000001",
            frame_id="FRM-000001",
            fragment_id="FRG-000001",
            parser_name="seed",
            role_name="raw_amount",
            value=100.0,
            confidence=0.95,
            extraction_mode="explicit",
            candidate_state="active",
        )
        slot = RoleSlotArtifact(
            role_name="raw_amount",
            active_claim_id=claim.claim_id,
            resolved_value=claim.value,
            confidence=claim.confidence,
        )
        frame = PartialFrameArtifact(
            frame_id="FRM-000001",
            parser_name="seed",
            frame_type="Observation",
            slots={"raw_amount": slot},
        )
        artifacts.claims.append(claim)
        artifacts.frames.append(frame)
        return artifacts


class SeedRowPass:
    def run(self, spec, artifacts, env):
        artifacts.rows.append(
            CanonicalRowArtifact(
                row_id="ROW-000001",
                frame_id="FRM-000001",
                parser_name="seed",
                frame_type="Observation",
                status="committed",
                raw_amount=10.0,
            )
        )
        return artifacts


def make_base_spec() -> ProgramSpec:
    spec = ProgramSpec(module_name="test_module")
    spec.frames["Observation"] = FrameSpec(
        name="Observation",
        fields=[FieldSpec(name="raw_amount", type_name="number")],
    )
    return spec


def test_repair_pass_uses_compiled_resolver_ir_even_if_syntax_policy_is_poisoned():
    spec = make_base_spec()
    spec.resolvers["Observation"] = ResolverPolicy(
        frame_name="Observation",
        commit_condition=BinaryExpr(NameExpr("score"), ">=", LiteralExpr(0.90)),
    )

    compiled = compile_program_spec(spec)
    compiled.syntax.resolvers["Observation"].commit_condition = LiteralExpr(False)

    runner = ESGPipelineRunner(passes=[SeedFramePass(), RepairPass()])
    result = runner.run(spec=compiled, fragments=[])

    frame = result.artifacts.frames[0]
    assert frame.status == "committed"
    assert frame.runtime.iteration_count >= 1
    assert frame.runtime.resolution_score >= 0.90


def test_default_runner_compiles_raw_spec_before_repair():
    spec = make_base_spec()
    spec.resolvers["Observation"] = ResolverPolicy(
        frame_name="Observation",
        commit_condition=BinaryExpr(NameExpr("score"), ">=", LiteralExpr(0.90)),
    )

    runner = ESGPipelineRunner(passes=[SeedFramePass(), RepairPass()])
    result = runner.run(spec=spec, fragments=[])

    assert isinstance(result.spec, CompiledProgramSpec)
    frame = result.artifacts.frames[0]
    assert frame.status == "committed"
    assert frame.runtime.resolution_score >= 0.90


def test_default_runner_raises_binding_error_for_unresolved_resolver_name():
    spec = make_base_spec()
    spec.resolvers["Observation"] = ResolverPolicy(
        frame_name="Observation",
        commit_condition=BinaryExpr(NameExpr("mystery_name"), "==", LiteralExpr(True)),
    )

    runner = ESGPipelineRunner(passes=[SeedFramePass(), RepairPass()])

    with pytest.raises(BindingError):
        runner.run(spec=spec, fragments=[])


def test_default_runner_rejects_frame_only_builtin_in_governance_host():
    spec = make_base_spec()
    spec.governances["Observation"] = GovernancePolicy(
        frame_name="Observation",
        merge_conditions=[
            FunctionCallExpr("missing", [NameExpr("raw_amount")]),
        ],
    )

    runner = ESGPipelineRunner(passes=[SeedRowPass(), GovernancePass()])

    with pytest.raises(BindingError):
        runner.run(spec=spec, fragments=[])


def test_governance_row_field_rule_still_merges_via_compiled_default_path():
    spec = make_base_spec()
    spec.governances["Observation"] = GovernancePolicy(
        frame_name="Observation",
        merge_conditions=[
            BinaryExpr(NameExpr("raw_amount"), ">", LiteralExpr(0)),
        ],
    )

    runner = ESGPipelineRunner(passes=[SeedRowPass(), GovernancePass()])
    result = runner.run(spec=spec, fragments=[])

    assert isinstance(result.spec, CompiledProgramSpec)
    row = result.artifacts.rows[0]
    decision = result.artifacts.merge_log[0]

    assert row.status == "merged"
    assert decision.action == "merge"
