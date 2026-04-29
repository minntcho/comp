from __future__ import annotations

from itertools import count
from typing import Any, Optional

from comp.artifacts import ClaimArtifact, CompileArtifacts, PartialFrameArtifact, RoleSlotArtifact, TokenOccurrence
from comp.dsl.compiled_spec import CompiledBindAction, CompiledParserInheritAction, CompiledProgramSpec, CompiledTagAction
from comp.eval.rule import RuleEvaluator
from comp.eval.source_module import SourceEvaluator
from comp.runtime_env import RuntimeEnv


class ParsePass:
    def __init__(self, source_evaluator: Optional[SourceEvaluator] = None, rule_evaluator: Optional[RuleEvaluator] = None) -> None:
        self.source_evaluator = source_evaluator or SourceEvaluator()
        self.rule_evaluator = rule_evaluator or RuleEvaluator()
        self._frame_seq = count(1)
        self._claim_seq = count(1)

    def run(self, spec: CompiledProgramSpec, artifacts: CompileArtifacts, env: RuntimeEnv) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("ParsePass requires CompiledProgramSpec")
        tokens_by_fragment = self._index_tokens(artifacts.tokens)
        new_frames: list[PartialFrameArtifact] = []
        new_claims: list[ClaimArtifact] = []
        for fragment in artifacts.fragments:
            frag_kind = self._fragment_kind(fragment)
            for parser_spec in spec.compiled_parsers.values():
                if frag_kind not in parser_spec.syntax.source_selectors:
                    continue
                frame = PartialFrameArtifact(
                    frame_id=f"FRM-{next(self._frame_seq):07d}",
                    parser_name=parser_spec.syntax.name,
                    frame_type=parser_spec.syntax.build_frame,
                    fragment_ids=[getattr(fragment, "fragment_id", "FRG-UNKNOWN")],
                    slots={},
                )
                ctx = self._build_eval_context(fragment, env, frame)
                for action in parser_spec.actions:
                    if isinstance(action, CompiledBindAction):
                        claims = self._resolve_source_to_claims(source_ir=action.source_ir, fragment=fragment, tokens_by_fragment=tokens_by_fragment, ctx=ctx, parser_name=parser_spec.syntax.name, frame_id=frame.frame_id, role_name=action.syntax.role_name, extraction_mode_override="explicit")
                        self._apply_role_binding(frame=frame, role_name=action.syntax.role_name, claims=claims, claims_out=new_claims, optional=action.syntax.optional, missing_tag_if_empty="missing_parser_failed")
                    elif isinstance(action, CompiledParserInheritAction):
                        if action.condition_ir is not None and not self.rule_evaluator.eval_bool(action.condition_ir, ctx):
                            continue
                        claims = self._resolve_source_to_claims(source_ir=action.source_ir, fragment=fragment, tokens_by_fragment=tokens_by_fragment, ctx=ctx, parser_name=parser_spec.syntax.name, frame_id=frame.frame_id, role_name=action.syntax.role_name, extraction_mode_override="inherited")
                        self._apply_role_binding(frame=frame, role_name=action.syntax.role_name, claims=claims, claims_out=new_claims, optional=True, missing_tag_if_empty="missing_waiting_context")
                    elif isinstance(action, CompiledTagAction):
                        claims = self._resolve_source_to_claims(source_ir=action.source_ir, fragment=fragment, tokens_by_fragment=tokens_by_fragment, ctx=ctx, parser_name=parser_spec.syntax.name, frame_id=frame.frame_id, role_name=action.syntax.role_name, extraction_mode_override="explicit")
                        self._apply_role_binding(frame=frame, role_name=action.syntax.role_name, claims=claims, claims_out=new_claims, optional=True, missing_tag_if_empty=None)
                    ctx.frame = frame
                    ctx.local_vars["status"] = frame.status
                new_frames.append(frame)
        artifacts.claims.extend(new_claims)
        artifacts.frames.extend(new_frames)
        return artifacts

    def _index_tokens(self, tokens: list[TokenOccurrence]) -> dict[str, dict[str, list[TokenOccurrence]]]:
        out: dict[str, dict[str, list[TokenOccurrence]]] = {}
        for tok in tokens:
            out.setdefault(tok.fragment_id, {}).setdefault(tok.token_name, []).append(tok)
        for frag_map in out.values():
            for bucket in frag_map.values():
                bucket.sort(key=lambda t: (-t.confidence, t.rank))
        return out

    def _resolve_source_to_claims(self, *, source_ir, fragment: Any, tokens_by_fragment: dict[str, dict[str, list[TokenOccurrence]]], ctx, parser_name: str, frame_id: str, role_name: str, extraction_mode_override: Optional[str] = None) -> list[ClaimArtifact]:
        candidates = self.source_evaluator.resolve(source_ir, ctx=ctx, fragment=fragment, tokens_by_fragment=tokens_by_fragment)
        claims: list[ClaimArtifact] = []
        fragment_id = getattr(fragment, "fragment_id", "FRG-UNKNOWN")
        for idx, cand in enumerate(candidates, start=1):
            claims.append(ClaimArtifact(claim_id=f"CLM-{next(self._claim_seq):07d}", frame_id=frame_id, fragment_id=fragment_id, parser_name=parser_name, role_name=role_name, value=cand.value, extraction_mode=extraction_mode_override or cand.extraction_mode, confidence=float(cand.confidence), candidate_state="active" if idx == 1 else "shadow", source_token_id=cand.source_token_id, source_fragment_id=cand.source_fragment_id or fragment_id, span=cand.span, metadata=dict(cand.metadata)))
        return claims

    def _apply_role_binding(self, *, frame: PartialFrameArtifact, role_name: str, claims: list[ClaimArtifact], claims_out: list[ClaimArtifact], optional: bool, missing_tag_if_empty: Optional[str]) -> None:
        slot = frame.slots.get(role_name)
        if slot is None:
            slot = RoleSlotArtifact(role_name=role_name)
            frame.slots[role_name] = slot
        if not claims:
            if slot.active_claim_id is None and missing_tag_if_empty is not None:
                slot.missing_tag = missing_tag_if_empty
                if missing_tag_if_empty not in slot.reason_codes:
                    slot.reason_codes.append(missing_tag_if_empty)
            return
        if slot.active_claim_id is None:
            claims[0].candidate_state = "active"
            slot.active_claim_id = claims[0].claim_id
            slot.resolved_value = claims[0].value
            slot.confidence = claims[0].confidence
            for c in claims[1:]:
                c.candidate_state = "shadow"
                slot.shadow_claim_ids.append(c.claim_id)
            slot.missing_tag = None
            claims_out.extend(claims)
            return
        for c in claims:
            c.candidate_state = "shadow"
            slot.shadow_claim_ids.append(c.claim_id)
        claims_out.extend(claims)

    def _build_eval_context(self, fragment: Any, env: RuntimeEnv, frame: PartialFrameArtifact):
        from comp.eval.expr import EvalContext
        metadata = getattr(fragment, "metadata", {}) or {}
        row = metadata.get("row", {}) if isinstance(metadata, dict) else {}
        row_label = metadata.get("row_label") if isinstance(metadata, dict) else None
        column_key = metadata.get("column_key") if isinstance(metadata, dict) else None
        return EvalContext(env=env, text=getattr(fragment, "text", ""), scope_path=getattr(fragment, "scope_path", tuple()), row=row, row_label=row_label, column_key=column_key, frame=frame, claims_by_id={}, local_vars={"frame_type": frame.frame_type, "status": frame.status})

    def _fragment_kind(self, fragment: Any) -> str:
        value = getattr(fragment, "fragment_type", None)
        return getattr(value, "value", value)


__all__ = ["ParsePass"]
