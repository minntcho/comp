from __future__ import annotations

import re
from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from comp.artifacts import ClaimArtifact, CompileArtifacts, PartialFrameArtifact, RoleSlotArtifact
from comp.dsl.compiled_spec import CompiledProgramSpec
from comp.dsl.spec_nodes import ContextPolicy
from comp.eval.rule import RuleEvaluator
from comp.eval.source_module import SourceEvaluator
from comp.runtime_env import RuntimeEnv, ScopePath


YEAR_ONLY_RE = re.compile(r"^20\d{2}$")
YEAR_MONTH_RE = re.compile(r"^20\d{2}-\d{2}$")


@dataclass
class CandidateView:
    claim: ClaimArtifact
    score: float
    source_scope_rank: int
    mode_rank: int
    specificity_rank: int


class ScopeResolutionPass:
    def __init__(self, rule_evaluator: Optional[RuleEvaluator] = None, source_evaluator: Optional[SourceEvaluator] = None) -> None:
        self.rule_evaluator = rule_evaluator or RuleEvaluator()
        self.source_evaluator = source_evaluator or SourceEvaluator()
        self._claim_seq = count(1)

    def run(self, spec: CompiledProgramSpec, artifacts: CompileArtifacts, env: RuntimeEnv) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("ScopeResolutionPass requires CompiledProgramSpec")
        fragments_by_id = self._index_fragments(artifacts.fragments)
        claims_by_id = {c.claim_id: c for c in artifacts.claims}
        new_claims: list[ClaimArtifact] = []
        for frame in artifacts.frames:
            base_scope = self._frame_scope(frame, fragments_by_id)
            frame_ctx = self._make_eval_context(env=env, scope_path=base_scope, frame=frame, claims_by_id=claims_by_id)
            added = self._apply_inherit_rules(spec=spec, frame=frame, frame_ctx=frame_ctx, fragments_by_id=fragments_by_id, claims_by_id=claims_by_id)
            for c in added:
                claims_by_id[c.claim_id] = c
            new_claims.extend(added)
            frame_fields = spec.frames.get(frame.frame_type)
            role_names = set(frame.slots.keys())
            if frame_fields is not None:
                role_names.update(f.name for f in frame_fields.fields)
            for role_name in role_names:
                slot = frame.slots.get(role_name)
                if slot is None:
                    slot = RoleSlotArtifact(role_name=role_name)
                    frame.slots[role_name] = slot
                policy = spec.contexts.get(role_name)
                self._resolve_slot_with_policy(frame=frame, slot=slot, role_name=role_name, policy=policy, claims_by_id=claims_by_id, fragments_by_id=fragments_by_id)
        artifacts.claims.extend(new_claims)
        return artifacts

    def _apply_inherit_rules(self, *, spec: CompiledProgramSpec, frame: PartialFrameArtifact, frame_ctx, fragments_by_id: dict[str, Any], claims_by_id: dict[str, ClaimArtifact]) -> list[ClaimArtifact]:
        created: list[ClaimArtifact] = []
        base_fragment = fragments_by_id.get(frame.fragment_ids[0]) if frame.fragment_ids else None
        for rule in spec.compiled_inherit_rules:
            role_name = rule.syntax.role_name
            slot = frame.slots.get(role_name)
            if slot is None:
                slot = RoleSlotArtifact(role_name=role_name)
                frame.slots[role_name] = slot
            if slot.active_claim_id is not None:
                continue
            if not self.rule_evaluator.eval_bool(rule.condition_ir, frame_ctx):
                continue
            source_candidates = self.source_evaluator.resolve(rule.source_ir, ctx=frame_ctx, fragment=base_fragment, tokens_by_fragment=None)
            if not source_candidates:
                if slot.missing_tag is None:
                    slot.missing_tag = "missing_waiting_context"
                if "missing_waiting_context" not in slot.reason_codes:
                    slot.reason_codes.append("missing_waiting_context")
                continue
            claims = []
            for idx, cand in enumerate(source_candidates, start=1):
                claims.append(ClaimArtifact(claim_id=f"CLM-{next(self._claim_seq):07d}", frame_id=frame.frame_id, fragment_id=frame.fragment_ids[0] if frame.fragment_ids else "FRG-UNKNOWN", parser_name=frame.parser_name, role_name=role_name, value=cand.value, extraction_mode=cand.extraction_mode or "inherited", confidence=float(cand.confidence), candidate_state="active" if idx == 1 else "shadow", source_token_id=cand.source_token_id, source_fragment_id=cand.source_fragment_id, span=cand.span, reason_codes=["inherited_from_context"], metadata=dict(cand.metadata)))
            slot.active_claim_id = claims[0].claim_id
            slot.resolved_value = claims[0].value
            slot.confidence = claims[0].confidence
            slot.missing_tag = None
            for c in claims[1:]:
                slot.shadow_claim_ids.append(c.claim_id)
            created.extend(claims)
        return created

    def _resolve_slot_with_policy(self, *, frame: PartialFrameArtifact, slot: RoleSlotArtifact, role_name: str, policy: Optional[ContextPolicy], claims_by_id: dict[str, ClaimArtifact], fragments_by_id: dict[str, Any]) -> None:
        candidate_ids = []
        if slot.active_claim_id:
            candidate_ids.append(slot.active_claim_id)
        candidate_ids.extend(slot.shadow_claim_ids)
        candidates = []
        for cid in candidate_ids:
            claim = claims_by_id.get(cid)
            if claim is None:
                continue
            candidates.append(self._score_candidate(claim=claim, role_name=role_name, policy=policy, fragments_by_id=fragments_by_id))
        if not candidates:
            if slot.missing_tag is None:
                slot.missing_tag = "missing_waiting_context"
                slot.reason_codes.append("missing_waiting_context")
            return
        candidates = self._apply_refine_resolution(role_name, policy, candidates)
        best, shadows, conflicted = self._pick_best_and_shadows(candidates)
        best.claim.candidate_state = "active"
        for s in shadows:
            s.claim.candidate_state = "shadow"
        slot.active_claim_id = best.claim.claim_id
        slot.shadow_claim_ids = [s.claim.claim_id for s in shadows]
        slot.resolved_value = best.claim.value
        slot.confidence = best.claim.confidence
        if conflicted:
            slot.reason_codes.append("context_conflict")
            if slot.missing_tag is None and best.mode_rank < 3:
                slot.missing_tag = "missing_conflicted"
        elif slot.missing_tag == "missing_conflicted":
            slot.missing_tag = None

    def _score_candidate(self, *, claim: ClaimArtifact, role_name: str, policy: Optional[ContextPolicy], fragments_by_id: dict[str, Any]) -> CandidateView:
        mode_rank = self._mode_rank(claim.extraction_mode)
        source_scope_rank = 0
        if policy is not None and claim.source_fragment_id is not None:
            source_scope_rank = self._scope_rank_for_claim(claim=claim, policy=policy, fragments_by_id=fragments_by_id)
        specificity_rank = self._specificity_rank(role_name, claim.value)
        score = mode_rank * 100.0 + float(claim.confidence) * 10.0 + source_scope_rank * 1.0 + specificity_rank * 0.1
        return CandidateView(claim=claim, score=score, source_scope_rank=source_scope_rank, mode_rank=mode_rank, specificity_rank=specificity_rank)

    def _mode_rank(self, extraction_mode: str) -> int:
        return {"explicit": 4, "inherited": 3, "backward_inferred": 2, "derived": 1}.get(extraction_mode, 0)

    def _scope_rank_for_claim(self, *, claim: ClaimArtifact, policy: ContextPolicy, fragments_by_id: dict[str, Any]) -> int:
        frag = fragments_by_id.get(claim.source_fragment_id)
        if frag is None:
            return 0
        scope_path = getattr(frag, "scope_path", tuple())
        levels = [getattr(s, "level", None) for s in scope_path]
        precedence = policy.precedence_chain or []
        for idx, label in enumerate(precedence):
            if label in levels:
                return len(precedence) - idx
        return 0

    def _specificity_rank(self, role_name: str, value: Any) -> int:
        if role_name == "period" and isinstance(value, str):
            if YEAR_MONTH_RE.fullmatch(value):
                return 2
            if YEAR_ONLY_RE.fullmatch(value):
                return 1
        return 0

    def _apply_refine_resolution(self, role_name: str, policy: Optional[ContextPolicy], candidates: list[CandidateView]) -> list[CandidateView]:
        if not candidates:
            return candidates
        if role_name != "period" or policy is None:
            return candidates
        has_period_refine = any(pair == ("YYYY_MM", "YYYY") for pair in policy.refine_pairs)
        if not has_period_refine:
            return candidates
        year_month_vals = {c.claim.value for c in candidates if isinstance(c.claim.value, str) and YEAR_MONTH_RE.fullmatch(c.claim.value)}
        out = []
        for c in candidates:
            if isinstance(c.claim.value, str) and YEAR_ONLY_RE.fullmatch(c.claim.value):
                year = c.claim.value
                if any(str(v).startswith(year + "-") for v in year_month_vals):
                    c = CandidateView(claim=c.claim, score=c.score - 0.5, source_scope_rank=c.source_scope_rank, mode_rank=c.mode_rank, specificity_rank=c.specificity_rank)
            out.append(c)
        return out

    def _pick_best_and_shadows(self, candidates: list[CandidateView]) -> tuple[CandidateView, list[CandidateView], bool]:
        candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        best = candidates[0]
        shadows = candidates[1:]
        conflicted = False
        if len(candidates) >= 2:
            second = candidates[1]
            if best.claim.value != second.claim.value and abs(best.score - second.score) < 0.75:
                conflicted = True
        return best, shadows, conflicted

    def _index_fragments(self, fragments: list[Any]) -> dict[str, Any]:
        return {getattr(f, "fragment_id", f"FRG-{i:06d}"): f for i, f in enumerate(fragments, start=1)}

    def _frame_scope(self, frame: PartialFrameArtifact, fragments_by_id: dict[str, Any]) -> ScopePath:
        if not frame.fragment_ids:
            return tuple()
        frag = fragments_by_id.get(frame.fragment_ids[0])
        if frag is None:
            return tuple()
        return getattr(frag, "scope_path", tuple())

    def _make_eval_context(self, *, env: RuntimeEnv, scope_path: ScopePath, frame: PartialFrameArtifact, claims_by_id: dict[str, ClaimArtifact]):
        from comp.eval.expr import EvalContext
        return EvalContext(env=env, text="", scope_path=scope_path, frame=frame, claims_by_id=claims_by_id, local_vars={"frame_type": frame.frame_type, "status": frame.status})


__all__ = ["CandidateView", "ScopeResolutionPass"]
