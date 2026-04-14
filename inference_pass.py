# inference_pass.py
from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from artifacts import (
    ClaimArtifact,
    CompileArtifacts,
    PartialFrameArtifact,
    RoleSlotArtifact,
)
from expr_eval import EvalContext, ExprEvaluator
from runtime_env import RuntimeEnv, ScopePath
from spec_nodes import InferSpec, ProgramSpec


@dataclass
class InferencePassConfig:
    """
    inference 결과를 기존 active와 비교할 때 쓰는 기본 마진.
    실제 resolver loop의 replace_margin보다 보수적으로 유지하는 편이 낫다.
    """
    strong_replace_margin: float = 0.05

    # infer "~" 는 prior/shadow 성격이 강하므로 기본적으로 active를 바로 뒤집지 않게 둔다.
    weak_infer_promotes_when_empty: bool = True

    # infer "=" 는 강한 inference이므로, 현 active가 매우 약하면 교체를 허용한다.
    strong_infer_can_replace_non_explicit: bool = True


class InferencePass:
    """
    partial frames -> enriched partial frames

    책임:
    1) infer 규칙 실행
    2) frame_type 강한 inference("=") 반영
    3) role 후보 backward_inferred claim 생성
    4) slot active/shadow 상태 업데이트

    설계 원칙:
    - infer "="  : strong inference
    - infer "~"  : shadow prior
    - 중복 value는 새 claim을 만들지 않고 기존 claim confidence를 보강
    """

    def __init__(
        self,
        evaluator: Optional[ExprEvaluator] = None,
        config: Optional[InferencePassConfig] = None,
    ) -> None:
        self.evaluator = evaluator or ExprEvaluator()
        self.config = config or InferencePassConfig()
        self._claim_seq = count(1)

    def run(
        self,
        spec: ProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        claims_by_id = {c.claim_id: c for c in artifacts.claims}
        fragments_by_id = {
            getattr(f, "fragment_id", f"FRG-{i:06d}"): f
            for i, f in enumerate(artifacts.fragments, start=1)
        }

        new_claims: list[ClaimArtifact] = []

        for frame in artifacts.frames:
            scope_path = self._frame_scope(frame, fragments_by_id)

            ctx = EvalContext(
                env=env,
                text="",
                scope_path=scope_path,
                frame=frame,
                claims_by_id=claims_by_id,
                local_vars={
                    "frame_type": frame.frame_type,
                    "status": frame.status,
                },
                warning_codes=self._frame_warning_codes(frame),
                error_codes=self._frame_error_codes(frame),
            )

            for rule in spec.infer_rules:
                if not self.evaluator.eval_bool(rule.condition, ctx):
                    continue

                inferred_values = self._normalize_values(
                    self.evaluator.eval(rule.value_expr, ctx)
                )
                if not inferred_values:
                    continue

                # 1) frame_type 강한 inference
                if rule.target_name == "frame_type":
                    changed = self._apply_frame_type_inference(
                        frame=frame,
                        rule=rule,
                        inferred_values=inferred_values,
                    )
                    if changed:
                        ctx.local_vars["frame_type"] = frame.frame_type
                    continue

                # 2) role inference
                created_or_updated = self._apply_role_inference(
                    frame=frame,
                    rule=rule,
                    inferred_values=inferred_values,
                    claims_by_id=claims_by_id,
                )

                for claim in created_or_updated:
                    # 새 claim만 여기 들어온다. 기존 claim confidence boost는 skip.
                    if claim.claim_id not in claims_by_id:
                        claims_by_id[claim.claim_id] = claim
                        new_claims.append(claim)

                # frame이 바뀌었으니 evaluator context 최신화
                ctx.frame = frame

        artifacts.claims.extend(new_claims)
        return artifacts

    # ------------------------------------------------------------------
    # Frame-type inference
    # ------------------------------------------------------------------

    def _apply_frame_type_inference(
        self,
        *,
        frame: PartialFrameArtifact,
        rule: InferSpec,
        inferred_values: list[Any],
    ) -> bool:
        """
        frame_type inference는 보통 '='만 허용하는 게 자연스럽다.
        값이 여러 개면 첫 번째만 사용.
        """
        if rule.op != "=":
            return False

        new_type = str(inferred_values[0]).strip()
        if not new_type:
            return False

        if frame.frame_type == new_type:
            return False

        frame.frame_type = new_type
        frame.diagnostics.append(
            {
                "severity": "info",
                "code": "FrameTypeInferred",
                "message": f"frame_type inferred as {new_type}",
                "rule_target": rule.target_name,
            }
        )
        return True

    # ------------------------------------------------------------------
    # Role inference
    # ------------------------------------------------------------------

    def _apply_role_inference(
        self,
        *,
        frame: PartialFrameArtifact,
        rule: InferSpec,
        inferred_values: list[Any],
        claims_by_id: dict[str, ClaimArtifact],
    ) -> list[ClaimArtifact]:
        slot = frame.slots.get(rule.target_name)
        if slot is None:
            slot = RoleSlotArtifact(role_name=rule.target_name)
            frame.slots[rule.target_name] = slot

        created: list[ClaimArtifact] = []

        for idx, value in enumerate(inferred_values, start=1):
            if value in (None, ""):
                continue

            existing = self._find_existing_claim_with_same_value(
                slot=slot,
                value=value,
                claims_by_id=claims_by_id,
            )

            # 같은 값이 이미 있으면 confidence만 보강
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
                reason_codes=[
                    f"inferred_by_rule:{rule.target_name}",
                    f"infer_op:{rule.op}",
                ],
                evidence_ids=[
                    f"pair:infer:{rule.target_name}:{rule.op}:{value}"
                ],
                metadata={
                    "inference_weight": rule.weight,
                    "inference_op": rule.op,
                },
            )

            promoted = self._maybe_promote_to_active(
                slot=slot,
                new_claim=new_claim,
                claims_by_id=claims_by_id,
                op=rule.op,
            )

            if not promoted:
                new_claim.candidate_state = "shadow"
                slot.shadow_claim_ids.append(new_claim.claim_id)
            else:
                slot.missing_tag = None

            created.append(new_claim)

        return created

    def _maybe_promote_to_active(
        self,
        *,
        slot: RoleSlotArtifact,
        new_claim: ClaimArtifact,
        claims_by_id: dict[str, ClaimArtifact],
        op: str,
    ) -> bool:
        """
        promotion 정책:
        - slot이 비어 있으면 infer "~" 도 active 허용 가능
        - infer "=" 는 stronger candidate로 간주
        - explicit active는 함부로 뒤집지 않는다
        """
        active_claim = (
            claims_by_id.get(slot.active_claim_id)
            if slot.active_claim_id is not None
            else None
        )

        # active 없음
        if active_claim is None:
            if op == "=":
                self._promote(slot, new_claim, claims_by_id)
                return True

            if op == "~" and self.config.weak_infer_promotes_when_empty:
                self._promote(slot, new_claim, claims_by_id)
                return True

            return False

        # active가 있는데, strong inference인지 확인
        if op != "=":
            return False

        if not self.config.strong_infer_can_replace_non_explicit:
            return False

        active_mode = active_claim.extraction_mode
        active_conf = float(active_claim.confidence)
        new_conf = float(new_claim.confidence)

        # explicit는 거의 보호
        if active_mode == "explicit":
            return False

        # inherited / backward_inferred / derived는 stronger inference로 교체 가능
        if new_conf >= active_conf + self.config.strong_replace_margin:
            self._promote(slot, new_claim, claims_by_id)
            return True

        return False

    def _promote(
        self,
        slot: RoleSlotArtifact,
        new_claim: ClaimArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> None:
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

    def _find_existing_claim_with_same_value(
        self,
        *,
        slot: RoleSlotArtifact,
        value: Any,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> Optional[ClaimArtifact]:
        ids = []
        if slot.active_claim_id:
            ids.append(slot.active_claim_id)
        ids.extend(slot.shadow_claim_ids)

        for cid in ids:
            claim = claims_by_id.get(cid)
            if claim is None:
                continue
            if claim.value == value:
                return claim
        return None

    def _boost_existing_claim(
        self,
        claim: ClaimArtifact,
        rule: InferSpec,
    ) -> None:
        new_conf = self._infer_confidence(rule, rank=1)
        if new_conf > claim.confidence:
            claim.confidence = new_conf

        tag = f"inferred_by_rule:{rule.target_name}"
        if tag not in claim.reason_codes:
            claim.reason_codes.append(tag)

        ev = f"pair:infer:{rule.target_name}:{rule.op}:{claim.value}"
        if ev not in claim.evidence_ids:
            claim.evidence_ids.append(ev)

    def _infer_confidence(self, rule: InferSpec, rank: int) -> float:
        """
        strong '=' inference는 좀 더 높게,
        '~'는 prior/shadow이므로 조금 낮게 시작.
        rank가 뒤로 갈수록 약간 감점.
        """
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

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _frame_scope(
        self,
        frame: PartialFrameArtifact,
        fragments_by_id: dict[str, Any],
    ) -> ScopePath:
        if not frame.fragment_ids:
            return tuple()

        frag = fragments_by_id.get(frame.fragment_ids[0])
        if frag is None:
            return tuple()

        return getattr(frag, "scope_path", tuple())

    def _frame_warning_codes(self, frame: PartialFrameArtifact) -> set[str]:
        codes = set()
        for d in getattr(frame, "diagnostics", []):
            if isinstance(d, dict) and d.get("severity") == "warning":
                code = d.get("code")
                if code:
                    codes.add(code)
        return codes

    def _frame_error_codes(self, frame: PartialFrameArtifact) -> set[str]:
        codes = set()
        for d in getattr(frame, "diagnostics", []):
            if isinstance(d, dict) and d.get("severity") == "error":
                code = d.get("code")
                if code:
                    codes.add(code)
        return codes