from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import count
from typing import Any, Optional

from artifacts import (
    ClaimArtifact,
    CompileArtifacts,
    PartialFrameArtifact,
    RoleSlotArtifact,
    diagnostic_codes,
)
from comp.compat.adapters import build_slot_selection_receipt
from compiled_spec import CompiledProgramSpec, CompiledResolverPolicy
from expr_eval import EvalContext
from rule_eval import RuleEvaluator
from runtime_env import RuntimeEnv


@dataclass
class RepairPassConfig:
    # DSL candidate_pool에 없더라도 엔진 기본값으로 둠
    freeze_after: int = 3
    drop_after: int = 6
    oscillation_window: int = 4

    # explicit 보호 정도
    explicit_protection_margin: float = 0.08

    # diagnostics에 따른 shadow 보너스
    conflict_shadow_bonus: float = 0.05
    mismatch_shadow_bonus: float = 0.08
    missing_shadow_bonus: float = 0.04

    trace_enabled: bool = True


@dataclass
class CandidateScore:
    claim_id: str
    total_score: float
    base_score: float
    mode_bonus: float
    aging_bonus: float
    diagnostic_bonus: float


class RepairPass:
    """
    frames -> repaired frames

    핵심 역할:
    1) slot별 active/shadow/frozen/rejected 재정렬
    2) aging 적용
    3) replace_margin 기반 교체
    4) frame-level score/stability 계산
    5) commit / review / reject 판정
    """

    def __init__(
        self,
        evaluator: RuleEvaluator | None = None,
        config: RepairPassConfig | None = None,
    ) -> None:
        self.evaluator = evaluator or RuleEvaluator()
        self.config = config or RepairPassConfig()
        self._event_seq = count(1)

    def run(
        self,
        spec: CompiledProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("RepairPass requires CompiledProgramSpec")

        claims_by_id = {c.claim_id: c for c in artifacts.claims}

        for frame in artifacts.frames:
            policy = spec.compiled_resolvers.get(frame.frame_type)
            if policy is None:
                continue

            self._repair_frame(
                frame=frame,
                policy=policy,
                claims_by_id=claims_by_id,
                env=env,
            )

        return artifacts

    # ------------------------------------------------------------------
    # Frame loop
    # ------------------------------------------------------------------

    def _repair_frame(
        self,
        *,
        frame: PartialFrameArtifact,
        policy: CompiledResolverPolicy,
        claims_by_id: dict[str, ClaimArtifact],
        env: RuntimeEnv,
    ) -> None:
        params = self._extract_policy_params(policy, env, frame, claims_by_id)

        max_iter = int(params.get("max_iter", 6))
        epsilon = float(params.get("epsilon", 0.02))
        replace_margin = float(params.get("replace_margin", 0.05))

        shadow_limit = int(params.get("candidate_pool.shadow", 2))
        allow_frozen = bool(params.get("candidate_pool.frozen", True))
        aging_step = float(params.get("candidate_pool.aging_step", 0.03))
        aging_cap = float(params.get("candidate_pool.aging_cap", 0.15))

        frame.metadata.setdefault("repair_trace", [])
        frame.metadata["resolver_frame_type"] = frame.frame_type

        prev_signature = None
        prev_score = 0.0
        no_improve_count = 0
        frame_stable = 0
        state_history: list[tuple] = []

        termination_reason = None
        last_iter_no = 0

        for iter_no in range(1, max_iter + 1):
            last_iter_no = iter_no

            # 1) diagnostics snapshot
            warning_codes = self._diag_codes(frame, severity="warning")
            error_codes = self._diag_codes(frame, severity="error")

            # 2) slot별 후보 재정렬
            for role_name, slot in frame.slots.items():
                self._revive_frozen_if_needed(
                    frame=frame,
                    slot=slot,
                    role_name=role_name,
                    claims_by_id=claims_by_id,
                    warning_codes=warning_codes,
                    error_codes=error_codes,
                    shadow_limit=shadow_limit,
                    allow_frozen=allow_frozen,
                )

                self._rerank_slot(
                    frame=frame,
                    slot=slot,
                    role_name=role_name,
                    claims_by_id=claims_by_id,
                    replace_margin=replace_margin,
                    aging_step=aging_step,
                    aging_cap=aging_cap,
                    shadow_limit=shadow_limit,
                    warning_codes=warning_codes,
                    error_codes=error_codes,
                )

            # 3) frame-level score / stability
            frame_score = self._frame_score(frame, claims_by_id)
            signature = self._frame_signature(frame)

            if prev_signature is not None and signature == prev_signature:
                frame_stable += 1
            else:
                frame_stable = 0

            if self.config.trace_enabled:
                frame.metadata["repair_trace"].append(
                    {
                        "iter": iter_no,
                        "frame_score": frame_score,
                        "frame_status": frame.status,
                        "frame_stable": frame_stable,
                        "signature": signature,
                        "warning_codes": sorted(warning_codes),
                        "error_codes": sorted(error_codes),
                        "slots": self._snapshot_slots(frame, claims_by_id),
                    }
                )

            # 4) commit condition
            eval_ctx = EvalContext(
                env=env,
                frame=frame,
                claims_by_id=claims_by_id,
                local_vars={
                    "score": frame_score,
                    "stable": frame_stable,
                    "status": frame.status,
                    "iteration": iter_no,
                    "no_improve_count": no_improve_count,
                },
                warning_codes=warning_codes,
                error_codes=error_codes,
            )

            if policy.commit_condition_ir is not None and self.evaluator.eval_bool(policy.commit_condition_ir, eval_ctx):
                frame.status = "committed"
                termination_reason = "commit_condition_satisfied"
                break

            # 5) seen state / oscillation
            if signature in state_history:
                termination_reason = "seen_state_repeated"
                break

            state_history.append(signature)

            if self._detect_oscillation(state_history):
                termination_reason = "oscillation_detected"
                break

            # 6) improvement
            improvement = frame_score - prev_score
            if improvement < epsilon:
                no_improve_count += 1
            else:
                no_improve_count = 0

            if no_improve_count >= 2:
                termination_reason = "no_meaningful_improvement"
                break

            prev_score = frame_score
            prev_signature = signature

        if last_iter_no > 0 and termination_reason is None:
            termination_reason = "max_iter_exhausted"

        final_score = self._frame_score(frame, claims_by_id)

        # loop 종료 후 최종 판정
        final_ctx = EvalContext(
            env=env,
            frame=frame,
            claims_by_id=claims_by_id,
            local_vars={
                "score": final_score,
                "stable": frame_stable,
                "status": frame.status,
                "iteration": last_iter_no,
                "no_improve_count": no_improve_count,
            },
            warning_codes=self._diag_codes(frame, severity="warning"),
            error_codes=self._diag_codes(frame, severity="error"),
        )

        if frame.status != "committed":
            if policy.review_condition_ir is not None and self.evaluator.eval_bool(policy.review_condition_ir, final_ctx):
                frame.status = "review_required"
            elif policy.syntax.reject_otherwise:
                frame.status = "rejected"
            else:
                frame.status = "resolving"

        frame.runtime.resolution_score = final_score
        frame.runtime.iteration_count = last_iter_no
        frame.runtime.stable_count = frame_stable
        frame.runtime.termination_reason = termination_reason

        # backward-compatible mirrors; read paths should prefer frame.runtime.
        frame.metadata["termination_reason"] = termination_reason
        frame.metadata["final_score"] = final_score
        self._store_selection_receipts(frame=frame, claims_by_id=claims_by_id, bundle_version=last_iter_no)

    # ------------------------------------------------------------------
    # Slot repair
    # ------------------------------------------------------------------

    def _rerank_slot(
        self,
        *,
        frame: PartialFrameArtifact,
        slot: RoleSlotArtifact,
        role_name: str,
        claims_by_id: dict[str, ClaimArtifact],
        replace_margin: float,
        aging_step: float,
        aging_cap: float,
        shadow_limit: int,
        warning_codes: set[str],
        error_codes: set[str],
    ) -> None:
        active_claim = claims_by_id.get(slot.active_claim_id) if slot.active_claim_id else None

        pool_ids = []
        if slot.active_claim_id:
            pool_ids.append(slot.active_claim_id)
        pool_ids.extend(slot.shadow_claim_ids)

        if not pool_ids:
            slot.missing_tag = slot.missing_tag or "missing_parser_failed"
            return

        scored: list[CandidateScore] = []

        for cid in pool_ids:
            claim = claims_by_id.get(cid)
            if claim is None:
                continue

            base = float(claim.confidence)
            mode_bonus = self._mode_bonus(claim)
            aging_bonus = self._aging_bonus(claim)
            diagnostic_bonus = self._diagnostic_bonus(
                role_name=role_name,
                claim=claim,
                slot=slot,
                warning_codes=warning_codes,
                error_codes=error_codes,
            )

            total = base + mode_bonus + aging_bonus + diagnostic_bonus

            claim.metadata["repair_score"] = {
                "base": base,
                "mode_bonus": mode_bonus,
                "aging_bonus": aging_bonus,
                "diagnostic_bonus": diagnostic_bonus,
                "total": total,
            }

            scored.append(
                CandidateScore(
                    claim_id=cid,
                    total_score=total,
                    base_score=base,
                    mode_bonus=mode_bonus,
                    aging_bonus=aging_bonus,
                    diagnostic_bonus=diagnostic_bonus,
                )
            )

        scored.sort(key=lambda s: s.total_score, reverse=True)
        best = scored[0]
        best_claim = claims_by_id[best.claim_id]

        if active_claim is None:
            self._promote_to_active(slot, best_claim, claims_by_id)
        else:
            if best_claim.claim_id != active_claim.claim_id:
                active_score = self._claim_total_score(active_claim)
                best_score = best.total_score

                if self._can_replace_active(
                    active_claim=active_claim,
                    active_score=active_score,
                    challenger=best_claim,
                    challenger_score=best_score,
                    replace_margin=replace_margin,
                ):
                    self._promote_to_active(slot, best_claim, claims_by_id)

        self._update_candidate_lifecycle(
            slot=slot,
            claims_by_id=claims_by_id,
            active_claim_id=slot.active_claim_id,
            aging_step=aging_step,
            aging_cap=aging_cap,
            shadow_limit=shadow_limit,
        )

        active = claims_by_id.get(slot.active_claim_id) if slot.active_claim_id else None
        if active is not None:
            slot.resolved_value = active.value
            slot.confidence = active.confidence
            if slot.missing_tag in {"missing_waiting_context", "missing_parser_failed", "missing_conflicted"}:
                slot.missing_tag = None

    def _revive_frozen_if_needed(
        self,
        *,
        frame: PartialFrameArtifact,
        slot: RoleSlotArtifact,
        role_name: str,
        claims_by_id: dict[str, ClaimArtifact],
        warning_codes: set[str],
        error_codes: set[str],
        shadow_limit: int,
        allow_frozen: bool,
    ) -> None:
        if not allow_frozen:
            return

        should_revive = False

        if slot.active_claim_id is None:
            should_revive = True

        if "context_conflict" in slot.reason_codes or slot.missing_tag == "missing_conflicted":
            should_revive = True

        if role_name in {"raw_unit", "activity_type"} and "UnitActivityMismatch" in error_codes:
            should_revive = True

        if role_name == "period" and "InvalidPeriod" in error_codes:
            should_revive = True

        if role_name == "site" and "MissingSite" in warning_codes:
            should_revive = True

        if not should_revive or not slot.frozen_claim_ids:
            return

        frozen_claims = [claims_by_id[cid] for cid in slot.frozen_claim_ids if cid in claims_by_id]
        frozen_claims.sort(key=lambda c: float(c.confidence), reverse=True)

        revive = frozen_claims[:1]
        revive_ids = {c.claim_id for c in revive}

        slot.frozen_claim_ids = [cid for cid in slot.frozen_claim_ids if cid not in revive_ids]
        for claim in revive:
            claim.candidate_state = "shadow"
            claim.metadata["not_selected_iters"] = 0
            slot.shadow_claim_ids.append(claim.claim_id)

        slot.shadow_claim_ids = slot.shadow_claim_ids[:shadow_limit]

    def _update_candidate_lifecycle(
        self,
        *,
        slot: RoleSlotArtifact,
        claims_by_id: dict[str, ClaimArtifact],
        active_claim_id: Optional[str],
        aging_step: float,
        aging_cap: float,
        shadow_limit: int,
    ) -> None:
        slot.shadow_claim_ids = [cid for cid in slot.shadow_claim_ids if cid != active_claim_id]

        new_shadow: list[str] = []
        new_frozen: list[str] = list(slot.frozen_claim_ids)
        new_rejected: list[str] = list(slot.rejected_claim_ids)

        for cid in slot.shadow_claim_ids:
            claim = claims_by_id.get(cid)
            if claim is None:
                continue

            not_selected_iters = int(claim.metadata.get("not_selected_iters", 0)) + 1
            claim.metadata["not_selected_iters"] = not_selected_iters

            aging_bonus = min(
                aging_cap,
                float(claim.metadata.get("aging_bonus", 0.0)) + aging_step,
            )
            claim.metadata["aging_bonus"] = aging_bonus

            if not_selected_iters >= self.config.drop_after:
                claim.candidate_state = "rejected"
                new_rejected.append(cid)
                continue

            if not_selected_iters >= self.config.freeze_after:
                claim.candidate_state = "frozen"
                new_frozen.append(cid)
                continue

            claim.candidate_state = "shadow"
            new_shadow.append(cid)

        if active_claim_id and active_claim_id in claims_by_id:
            active = claims_by_id[active_claim_id]
            active.candidate_state = "active"
            active.metadata["aging_bonus"] = 0.0
            active.metadata["not_selected_iters"] = 0

        new_shadow.sort(
            key=lambda cid: -self._claim_total_score(claims_by_id[cid]) if cid in claims_by_id else 0.0
        )
        slot.shadow_claim_ids = new_shadow[:shadow_limit]
        slot.frozen_claim_ids = new_frozen
        slot.rejected_claim_ids = new_rejected

    def _promote_to_active(
        self,
        slot: RoleSlotArtifact,
        claim: ClaimArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> None:
        old_active_id = slot.active_claim_id
        if old_active_id and old_active_id != claim.claim_id:
            old_active = claims_by_id.get(old_active_id)
            if old_active is not None:
                old_active.candidate_state = "shadow"
                if old_active_id not in slot.shadow_claim_ids:
                    slot.shadow_claim_ids.append(old_active_id)

        slot.active_claim_id = claim.claim_id
        claim.candidate_state = "active"

        if claim.claim_id in slot.shadow_claim_ids:
            slot.shadow_claim_ids.remove(claim.claim_id)

    def _store_selection_receipts(
        self,
        *,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
        bundle_version: int,
    ) -> None:
        receipts = []
        for role_name, slot in sorted(frame.slots.items()):
            receipt = build_slot_selection_receipt(
                frame=frame,
                role_name=role_name,
                slot=slot,
                claims_by_id=claims_by_id,
                bundle_version=bundle_version,
            )
            receipts.append(asdict(receipt))
        frame.metadata["selection_receipts"] = receipts

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _mode_bonus(self, claim: ClaimArtifact) -> float:
        return {
            "explicit": 0.10,
            "inherited": 0.05,
            "backward_inferred": 0.00,
            "derived": -0.02,
        }.get(claim.extraction_mode, 0.0)

    def _aging_bonus(self, claim: ClaimArtifact) -> float:
        return float(claim.metadata.get("aging_bonus", 0.0))

    def _diagnostic_bonus(
        self,
        *,
        role_name: str,
        claim: ClaimArtifact,
        slot: RoleSlotArtifact,
        warning_codes: set[str],
        error_codes: set[str],
    ) -> float:
        bonus = 0.0

        if "context_conflict" in slot.reason_codes or slot.missing_tag == "missing_conflicted":
            if claim.candidate_state == "shadow":
                bonus += self.config.conflict_shadow_bonus

        if role_name in {"raw_unit", "activity_type"} and "UnitActivityMismatch" in error_codes:
            if claim.candidate_state == "shadow":
                bonus += self.config.mismatch_shadow_bonus

        if role_name == "period" and "InvalidPeriod" in error_codes:
            if claim.candidate_state == "shadow":
                bonus += self.config.mismatch_shadow_bonus

        if role_name == "site" and "MissingSite" in warning_codes:
            if claim.extraction_mode in {"inherited", "backward_inferred"}:
                bonus += self.config.missing_shadow_bonus

        return bonus

    def _claim_total_score(self, claim: ClaimArtifact) -> float:
        data = claim.metadata.get("repair_score")
        if isinstance(data, dict) and "total" in data:
            return float(data["total"])
        return float(claim.confidence)

    def _frame_score(
        self,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> float:
        scores = []
        completeness_penalty = 0.0

        for slot in frame.slots.values():
            if slot.active_claim_id and slot.active_claim_id in claims_by_id:
                scores.append(self._claim_total_score(claims_by_id[slot.active_claim_id]))
            else:
                completeness_penalty += 0.10

        if not scores:
            return 0.0

        avg = sum(scores) / len(scores)
        return max(0.0, avg - completeness_penalty)

    def _can_replace_active(
        self,
        *,
        active_claim: ClaimArtifact,
        active_score: float,
        challenger: ClaimArtifact,
        challenger_score: float,
        replace_margin: float,
    ) -> bool:
        margin = replace_margin
        if active_claim.extraction_mode == "explicit":
            margin += self.config.explicit_protection_margin

        return challenger_score >= active_score + margin

    # ------------------------------------------------------------------
    # Loop helpers
    # ------------------------------------------------------------------

    def _frame_signature(self, frame: PartialFrameArtifact) -> tuple:
        items = []
        for role_name in sorted(frame.slots.keys()):
            slot = frame.slots[role_name]
            items.append((role_name, slot.active_claim_id, slot.missing_tag))
        return tuple(items)

    def _detect_oscillation(self, state_history: list[tuple]) -> bool:
        win = self.config.oscillation_window
        if len(state_history) < win:
            return False

        tail = state_history[-win:]
        if win == 4:
            a, b, c, d = tail
            return (a == c) and (b == d) and (a != b)

        unique = list(dict.fromkeys(tail))
        return len(unique) == 2 and tail[0] == tail[2] and tail[1] == tail[3]

    def _snapshot_slots(
        self,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> dict[str, Any]:
        out = {}
        for role_name, slot in frame.slots.items():
            active = claims_by_id.get(slot.active_claim_id) if slot.active_claim_id else None
            out[role_name] = {
                "active_claim_id": slot.active_claim_id,
                "active_value": None if active is None else active.value,
                "active_mode": None if active is None else active.extraction_mode,
                "active_score": None if active is None else self._claim_total_score(active),
                "shadow_count": len(slot.shadow_claim_ids),
                "frozen_count": len(slot.frozen_claim_ids),
                "rejected_count": len(slot.rejected_claim_ids),
                "missing_tag": slot.missing_tag,
                "reason_codes": list(slot.reason_codes),
            }
        return out

    def _diag_codes(
        self,
        frame: PartialFrameArtifact,
        *,
        severity: str,
    ) -> set[str]:
        return set(diagnostic_codes(frame.diagnostics, severity=severity))

    def _extract_policy_params(
        self,
        policy: CompiledResolverPolicy,
        env: RuntimeEnv,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> dict[str, Any]:
        """
        resolver block의 literal-ish assign들을 실제 값으로 평가.
        """
        params: dict[str, Any] = {}

        ctx = EvalContext(
            env=env,
            frame=frame,
            claims_by_id=claims_by_id,
            local_vars={},
        )

        for key, expr in policy.assigns_ir.items():
            params[key] = self.evaluator.eval(expr, ctx)

        for key, expr in policy.candidate_pool_assigns_ir.items():
            params[f"candidate_pool.{key}"] = self.evaluator.eval(expr, ctx)

        return params
