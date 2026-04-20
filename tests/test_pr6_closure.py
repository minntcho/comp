from __future__ import annotations

import unittest

from artifacts import CanonicalRowArtifact, ClaimArtifact, CompileArtifacts, PartialFrameArtifact, RoleSlotArtifact
from ast_nodes import BinaryExpr, FunctionCallExpr, NameExpr
from binder import Binder, BindingError
from esg_builtins import register_default_builtins
from calculation_pass import CalculationPass
from emit_pass import EmitPass
from governance_pass import GovernancePass
from pipeline_runner import build_default_passes
from runtime_env import build_runtime_env
from semantic_pass import SemanticPass, SemanticPassConfig
from spec_nodes import ActivitySpec, ConstraintSpec, FieldSpec, FrameSpec, GovernancePolicy, ProgramSpec


class PR6ClosureTests(unittest.TestCase):
    def _make_program_spec(self) -> ProgramSpec:
        return ProgramSpec(
            module_name="test_module",
            activities={
                "electricity": ActivitySpec(
                    name="electricity",
                    dimension="energy",
                    scope_category="scope2",
                )
            },
            frames={
                "ActivityObservation": FrameSpec(
                    name="ActivityObservation",
                    fields=[
                        FieldSpec(name="activity_type", type_name="str"),
                        FieldSpec(name="raw_amount", type_name="number"),
                    ],
                )
            },
            constraints=[
                ConstraintSpec(
                    kind="require",
                    condition=FunctionCallExpr("valid", [NameExpr("raw_amount")]),
                    frame_name="ActivityObservation",
                )
            ],
            governances={
                "ActivityObservation": GovernancePolicy(
                    frame_name="ActivityObservation",
                    merge_conditions=[
                        BinaryExpr(NameExpr("status"), "==", NameExpr("committed"))
                    ],
                )
            },
        )

    def _make_env(self, spec: ProgramSpec):
        env = build_runtime_env(spec)
        register_default_builtins(env)
        return env

    def _make_artifacts(self) -> CompileArtifacts:
        claim = ClaimArtifact(
            claim_id="CLM-0000001",
            frame_id="FRM-0000001",
            fragment_id="FRG-0000001",
            parser_name="parser.activity",
            role_name="activity_type",
            value="electricity",
            extraction_mode="explicit",
            confidence=0.95,
            candidate_state="active",
            status="resolved",
            source_fragment_id="FRG-0000001",
        )
        slot = RoleSlotArtifact(
            role_name="activity_type",
            active_claim_id=claim.claim_id,
            resolved_value=claim.value,
            confidence=claim.confidence,
        )
        frame = PartialFrameArtifact(
            frame_id="FRM-0000001",
            parser_name="parser.activity",
            frame_type="ActivityObservation",
            fragment_ids=["FRG-0000001"],
            slots={"activity_type": slot},
            status="committed",
        )
        return CompileArtifacts(
            fragments=[],
            claims=[claim],
            frames=[frame],
        )

    def test_build_default_passes_uses_distinct_semantic_phases(self):
        passes = build_default_passes(include_post_repair_semantic=True)
        phase_labels = [p.config.phase_label for p in passes if isinstance(p, SemanticPass)]
        self.assertEqual(["semantic_pre", "semantic_post"], phase_labels)

    def test_binder_rejects_unresolved_rule_name(self):
        spec = ProgramSpec(
            module_name="broken_module",
            frames={
                "ActivityObservation": FrameSpec(name="ActivityObservation", fields=[])
            },
            constraints=[
                ConstraintSpec(
                    kind="require",
                    condition=NameExpr("ghost_symbol"),
                    frame_name="ActivityObservation",
                )
            ],
        )
        with self.assertRaises(BindingError):
            Binder().bind(spec)

    def test_semantic_pre_and_post_both_survive_on_frame(self):
        spec = self._make_program_spec()
        compiled = Binder().bind(spec)
        env = self._make_env(spec)
        artifacts = self._make_artifacts()

        artifacts = SemanticPass(
            config=SemanticPassConfig(phase_label="semantic_pre")
        ).run(compiled, artifacts, env)
        artifacts = SemanticPass(
            config=SemanticPassConfig(phase_label="semantic_post")
        ).run(compiled, artifacts, env)

        phases = {diag.phase for diag in artifacts.frames[0].diagnostics}
        self.assertIn("semantic_pre", phases)
        self.assertIn("semantic_post", phases)

    def test_semantic_error_reaches_row_and_governance_holds(self):
        spec = self._make_program_spec()
        compiled = Binder().bind(spec)
        env = self._make_env(spec)
        artifacts = self._make_artifacts()

        artifacts = SemanticPass().run(compiled, artifacts, env)
        artifacts = EmitPass().run(compiled, artifacts, env)
        artifacts = GovernancePass().run(compiled, artifacts, env)

        self.assertEqual(1, len(artifacts.rows))
        row = artifacts.rows[0]
        self.assertIn("RequireViolation", row.error_codes)
        self.assertEqual("hold", artifacts.merge_log[-1].action)
        self.assertIn("row_has_error_diagnostics", artifacts.merge_log[-1].reason_codes)

    def test_calculation_excludes_merged_row_with_errors(self):
        spec = ProgramSpec(module_name="calc_module")
        env = self._make_env(spec)
        row = CanonicalRowArtifact(
            row_id="ROW-0000001",
            frame_id="FRM-0000001",
            parser_name="parser.activity",
            frame_type="ActivityObservation",
            status="merged",
            activity_type="electricity",
            standardized_amount=1.0,
            standardized_unit="kwh",
            error_codes=["RequireViolation"],
        )
        artifacts = CompileArtifacts(rows=[row])

        artifacts = CalculationPass().run(None, artifacts, env)

        self.assertEqual(1, len(artifacts.calculations))
        calc = artifacts.calculations[0]
        self.assertEqual("excluded", calc.calculation_status)
        self.assertEqual("row_has_error_diagnostics", calc.exclusion_reason)


if __name__ == "__main__":
    unittest.main()
