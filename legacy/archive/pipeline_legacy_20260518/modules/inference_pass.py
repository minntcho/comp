from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any

from artifacts import (
    ClaimArtifact,
    CompileArtifacts,
    DiagnosticArtifact,
    PartialFrameArtifact,
    RoleSlotArtifact,
    error_codes_from_diagnostics,
    warning_codes_from_diagnostics,
)
from compiled_spec import CompiledProgramSpec
from expr_eval import EvalContext
from rule_eval import RuleEvaluator
from runtime_env import RuntimeEnv, ScopePath


@dataclass
class InferencePassConfig:
    strong_replace_margin: float = 0.05
    weak_infer_promotes_when_empty: bool = True
    strong_infer_can_replace_non_explicit: bool = True


class InferencePass:
    def __init__(self, evaluator: RuleEvaluator | None = None, config: InferencePassConfig | None = None) -> None:
        self.evaluator = evaluator or RuleEvaluator()
        self.config = config or InferencePassConfig()
        self._claim_seq = count(1)
        self._diag_seq = count(1)

    def run(self, spec: CompiledProgramSpec, artifacts: CompileArtifacts, env: RuntimeEnv) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("InferencePass requires CompiledProgramSpec")

        claims_by_id = {c.claim_id: c for c in artifacts.claims}
        fragments_by_id = {getattr(f, "fragment_id", f"FRG-{i:06d}"): f for i, f in enumerate(artifacts.fragments, start=1)}
        new_claims: list[ClaimArtifact] = []

        for frame in artifacts.frames:
            ctx = EvalContext(
                env=env,
                text="",
                scope_path=self._frame_scope(frame, fragments_by_id),
                frame=frame,
                claims_by_id=claims_by_id,
                local_vars={"frame_type": frame.frame_type, "status": frame.status},
                warning_codes=self._frame_warning_codes(frame),
                error_codes=self._frame_error_codes(frame),
            )

            for compiled_rule in spec.compiled_infer_rules:
                rule = compiled_rule.syntax
                if not self.evaluator.eval_bool(compiled_rule.condition_ir, ctx):
                    continue

                inferred_values = self._normalize_values(self.evaluator.eval(compiled_rule.value_ir, ctx))
                if not inferred_values:
                    continue

                if rule.target_name == "frame_type":
                    changed = self._apply_frame_type_inference(frame=frame, rule=rule, inferred_values=inferred_values)
                    if changed:
                        ctx.local_vars["frame_type"] = frame.frame_type
                    continue

                created_or_updated = self._apply_role_inference(
                    frame=frame,
                    rule=rule,
                    inferred_values=inferred_values,
                    claims_by_id=claims_by_id,
                )
                for claim in created_or_updated:
                    if claim.claim_id not in claims_by_id:
                        claims_by_id[claim.claim_id] = claim
                        new_claims.append(claim)
                ctx.frame = frame

        artifacts.claims.extend(new_claims)
        return artifacts

    def _apply_frame_type_inference(self, *, frame: PartialFrameArtifact, rule, inferred_values: list[Any]) -> bool:
        if rule.op != "=":
            return False
        new_type = str(inferred_values[0]).strip()
        if not new_type or frame.frame_type == new_type:
            return False

        frame.frame_type = new_type
        frame.diagnostics.append(
            DiagnosticArtifact(
                diagnostic_id=f"DGN-INF-{next(self._diag_seq):07d}",
                severity="info",
                code="FrameTypeInferred",
                message=f"frame_type inferred as {new_type}",
                scope_kind="frame",
                scope_id=frame.frame_id,
                frame_id=frame.frame_id,
                fragment_id=frame.fragment_ids[0] if frame.fragment_ids else None,
                rule_kind="inference",
                source_key=f"infer:{rule.target_name}",
                phase="inference",
                metadata={"rule_target": rule.target_name},
            )
        )
        return True

    def _apply_role_inference(self, *, frame: PartialFrameArtifact, rule, inferred_values: list[Any], claims_by_id: dict[str, ClaimArtifact]) -> list[ClaimArtifact]:
        slot = frame.slots.get(rule.target_name)
        if slot is None:
            slot = RoleSlotArtifact(role_name=rule.target_name)
            frame.slots[rule.target_name] = slot

        created: list[ClaimArtifact] = []
        for idx, value in enumerate(inferred_values, start=1):
            if value in (None, ""):
                continue

            existing = self._find_existing_claim_with_same_value(slot=slot, value=value, claims_by_id=claims_by_id)
            if existing is not None:
                self._boost_existing_claim(existing, rule)
                continue

            new_claim = ClaimArtifact(
                claim_id=f"CLM-{next(self._claim_seq):07d}",
                frame_id=frame.frame_id,
                fragment_id=frame.fragment_ids[0] if frame.fragment_ids else "FRG-UNKNOWN",
                parser_name=frame.parser_name,
                role_name=rule.target_name,
                value=value,
                extraction_mode="backward_inferred",
                confidence=self._infer_confidence(rule, rank=idx),
                candidate_state="shadow",
                status="resolving",
                source_fragment_id=frame.fragment_ids[0] if frame.fragment_ids else None,
                span=None,
                reason_codes=[f"inferred_by_rule:{rule.target_name}", f"infer_op:{rule.op}"],
                evidence_ids=[f"pair:infer:{rule.target_name}:{rule.op}:{value}"],
                metadata={"inference_weight": rule.weight, "inference_op": rule.op},
            )

            promoted = self._maybe_promote_to_active(slot=slot, new_claim=new_claim, claims_by_id=claims_by_id, op=rule.op)
            if not promoted:
                new_claim.candidate_state = "shadow"
                slot.shadow_claim_ids.append(new_claim.claim_id)
            else:
                slot.missing_tag = None
            created.append(new_claim)

        return created

    def _maybe_promote_to_active(self, *, slot: RoleSlotArtifact, new_claim: ClaimArtifact, claims_by_id: dict[str, ClaimArtifact], op: str) -> bool:
        active_claim = claims_by_id.get(slot.active_claim_id) if slot.active_claim_id is not None else None
        if active_claim is None:
            if op == "=" or (op == "~" and self.config.weak_infer_promotes_when_empty):
                self._promote(slot, new_claim, claims_by_id)
                return True
            return False

        if op != "=" or not self.config.strong_infer_can_replace_non_explicit or active_claim.extraction_mode == "explicit":
            return False
        return self._promote_if_stronger(slot, active_claim, new_claim, claims_by_id)

    def _promote_if_stronger(self, slot, active_claim, new_claim, claims_by_id) -> bool:
        active_conf = float(active_claim.confidence)
        new_conf = float(new_claim.confidence)
        if new_conf >= active_conf + self.config.strong_replace_margin:
            self._promote(slot, new_claim, claims_by_id)
            return True
        return False

    def _promote(self, slot: RoleSlotArtifact, new_claim: ClaimArtifact, claims_by_id: dict[str, ClaimArtifact]) -> None:
        old_active_id = slot.active_claim_id
        if old_active_id is not None:
            old_active = claims_by_id.get(old_active_id)
            if old_active is not None:
                old_active.candidate_state = "shadow"
            if old_active_id not in slot.shadow_claim_ids:
                slot.shadow_claim_ids.append(old_active_id)
        new_claim.candidate_state = "active"
        slot.active_claim_id = new_claim.claim_id
        slot.resolved_value = new_claim.value
        slot.confidence = new_claim.confidence

    def _find_existing_claim_with_same_value(self, *, slot: RoleSlotArtifact, value: Any, claims_by_id: dict[str, ClaimArtifact]) -> ClaimArtifact | None:
        ids = ([slot.active_claim_id] if slot.active_claim_id else []) + list(slot.shadow_claim_ids)
        for cid in ids:
            claim = claims_by_id.get(cid)
            if claim is not None and claim.value == value:
                return claim
        return None

    def _boost_existing_claim(self, claim: ClaimArtifact, rule) -> None:
        new_conf = self._infer_confidence(rule, rank=1)
        if new_conf > claim.confidence:
            claim.confidence = new_conf
        tag = f"inferred_by_rule:{rule.target_name}"
        if tag not in claim.reason_codes:
            claim.reason_codes.append(tag)
        ev = f"pair:infer:{rule.target_name}:{rule.op}:{claim.value}"
        if ev not in claim.evidence_ids:
            claim.evidence_ids.append(ev)

    def _infer_confidence(self, rule, rank: int) -> float:
        base = rule.weight if rule.weight is not None else (0.90 if rule.op == "=" else 0.70)
        penalty = (rank - 1) * 0.05
        return max(0.0, min(1.0, float(base) - penalty))

    def _normalize_values(self, value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            out: list[Any] = []
            for item in value:
                out.extend(self._normalize_values(item))
            return out
        return [value]

    def _frame_scope(self, frame: PartialFrameArtifact, fragments_by_id: dict[str, Any]) -> ScopePath:
        if not frame.fragment_ids:
            return tuple()
        frag = fragments_by_id.get(frame.fragment_ids[0])
        if frag is None:
            return tuple()
        return getattr(frag, "scope_path", tuple())

    def _frame_warning_codes(self, frame: PartialFrameArtifact) -> set[str]:
        return set(warning_codes_from_diagnostics(frame.diagnostics))

    def _frame_error_codes(self, frame: PartialFrameArtifact) -> set[str]:
        return set(error_codes_from_diagnostics(frame.diagnostics))
