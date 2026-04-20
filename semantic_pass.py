from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any

from artifacts import CompileArtifacts, DiagnosticArtifact, PartialFrameArtifact
from compiled_spec import CompiledProgramSpec
from expr_eval import EvalContext
from rule_eval import RuleEvaluator
from runtime_env import RuntimeEnv


@dataclass
class SemanticPassConfig:
    phase_label: str = "semantic_pre"
    dedupe: bool = True
    clear_same_phase_before_run: bool = True


class SemanticPass:
    def __init__(
        self,
        evaluator: RuleEvaluator | None = None,
        config: SemanticPassConfig | None = None,
    ) -> None:
        self.evaluator = evaluator or RuleEvaluator()
        self.config = config or SemanticPassConfig()
        self._diag_seq = count(1)

    def run(
        self,
        spec: CompiledProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("SemanticPass requires CompiledProgramSpec")

        claims_by_id = {c.claim_id: c for c in artifacts.claims}
        if self.config.clear_same_phase_before_run:
            self._clear_same_phase(artifacts)

        new_global_diags: list[DiagnosticArtifact] = []

        for frame in artifacts.frames:
            frame_diags: list[DiagnosticArtifact] = []
            ctx = EvalContext(
                env=env,
                text="",
                scope_path=self._frame_scope(frame, artifacts.fragments),
                frame=frame,
                claims_by_id=claims_by_id,
                local_vars={"frame_type": frame.frame_type, "status": frame.status},
                warning_codes=self._existing_codes(frame, severity="warning"),
                error_codes=self._existing_codes(frame, severity="error"),
            )

            for idx, compiled_constraint in enumerate(spec.compiled_constraints, start=1):
                constraint = compiled_constraint.syntax
                if constraint.frame_name is not None and constraint.frame_name != frame.frame_type:
                    continue

                if constraint.kind == "require":
                    passed = self.evaluator.eval_bool(compiled_constraint.condition_ir, ctx)
                    if not passed:
                        diag = self._make_diagnostic(
                            severity="error",
                            code="RequireViolation",
                            message=f"require failed on frame {frame.frame_id}",
                            frame=frame,
                            rule_kind="require",
                            source_key=f"require:{idx}",
                        )
                        if self._accept_diag(frame, diag):
                            frame_diags.append(diag)
                            ctx.error_codes.add(diag.code)
                elif constraint.kind == "forbid":
                    violated = self.evaluator.eval_bool(compiled_constraint.condition_ir, ctx)
                    if violated:
                        diag = self._make_diagnostic(
                            severity="error",
                            code="ForbidViolation",
                            message=f"forbid violated on frame {frame.frame_id}",
                            frame=frame,
                            rule_kind="forbid",
                            source_key=f"forbid:{idx}",
                        )
                        if self._accept_diag(frame, diag):
                            frame_diags.append(diag)
                            ctx.error_codes.add(diag.code)

            for compiled_rule in spec.compiled_diagnostics:
                rule = compiled_rule.syntax
                if not self.evaluator.eval_bool(compiled_rule.condition_ir, ctx):
                    continue

                diag = self._make_diagnostic(
                    severity=rule.level,
                    code=rule.code,
                    message=f"{rule.code} triggered on frame {frame.frame_id}",
                    frame=frame,
                    rule_kind="diagnostic",
                    source_key=f"{rule.level}:{rule.code}",
                )
                if self._accept_diag(frame, diag):
                    frame_diags.append(diag)
                    if rule.level == "warning":
                        ctx.warning_codes.add(rule.code)
                    elif rule.level == "error":
                        ctx.error_codes.add(rule.code)

            frame.diagnostics.extend(frame_diags)
            new_global_diags.extend(frame_diags)

        artifacts.diagnostics.extend(new_global_diags)
        return artifacts

    def _make_diagnostic(
        self,
        *,
        severity: str,
        code: str,
        message: str,
        frame: PartialFrameArtifact,
        rule_kind: str,
        source_key: str,
    ) -> DiagnosticArtifact:
        return DiagnosticArtifact(
            diagnostic_id=f"DGN-{next(self._diag_seq):07d}",
            severity=severity,
            code=code,
            message=message,
            scope_kind="frame",
            scope_id=frame.frame_id,
            frame_id=frame.frame_id,
            fragment_id=frame.fragment_ids[0] if frame.fragment_ids else None,
            rule_kind=rule_kind,
            source_key=source_key,
            phase=self.config.phase_label,
        )

    def _accept_diag(self, frame: PartialFrameArtifact, diag: DiagnosticArtifact) -> bool:
        if not self.config.dedupe:
            return True

        key = (diag.phase, diag.severity, diag.code, diag.source_key)
        for existing in frame.diagnostics:
            old_key = (
                getattr(existing, "phase", None),
                getattr(existing, "severity", None),
                getattr(existing, "code", None),
                getattr(existing, "source_key", None),
            )
            if old_key == key:
                return False
        return True

    def _clear_same_phase(self, artifacts: CompileArtifacts) -> None:
        phase = self.config.phase_label
        for frame in artifacts.frames:
            frame.diagnostics = [d for d in frame.diagnostics if getattr(d, "phase", None) != phase]
        artifacts.diagnostics = [d for d in artifacts.diagnostics if getattr(d, "phase", None) != phase]

    def _existing_codes(self, frame: PartialFrameArtifact, *, severity: str) -> set[str]:
        codes = set()
        for d in frame.diagnostics:
            if getattr(d, "severity", None) == severity:
                code = getattr(d, "code", None)
                if code:
                    codes.add(code)
        return codes

    def _frame_scope(self, frame: PartialFrameArtifact, fragments: list[Any]):
        frag_map = {getattr(f, "fragment_id", f"FRG-{i:06d}"): f for i, f in enumerate(fragments, start=1)}
        if not frame.fragment_ids:
            return tuple()
        frag = frag_map.get(frame.fragment_ids[0])
        if frag is None:
            return tuple()
        return getattr(frag, "scope_path", tuple())
