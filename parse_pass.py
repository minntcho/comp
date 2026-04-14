# parse_pass.py
from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from artifacts import (
    ClaimArtifact,
    CompileArtifacts,
    PartialFrameArtifact,
    RoleSlotArtifact,
    TokenOccurrence,
)
from ast_nodes import (
    AlternationExpr,
    ColumnRefExpr,
    ContextRefExpr,
    Expr,
    NameExpr,
    ParserInheritStmt,
    BindStmt,
    RowLabelRefExpr,
    TagStmt,
)
from expr_eval import EvalContext, ExprEvaluator
from runtime_env import ContextEntry, RuntimeEnv
from spec_nodes import ParserSpec, ProgramSpec


@dataclass
class SourceCandidate:
    value: Any
    confidence: float
    extraction_mode: str             # explicit | inherited | derived ...
    source_token_id: Optional[str] = None
    source_fragment_id: Optional[str] = None
    span: Optional[tuple[int, int]] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ParsePass:
    """
    tokens -> partial frames

    설계 원칙:
    - parser source expr의 AlternationExpr는 left-biased fallback
      예: column("항목") | ActivityToken
    - token ref(NameExpr)는 현재 fragment의 token pool에서 찾음
    - bind/tag/inherit는 모두 role slot을 갱신하지만,
      extraction_mode와 missing_tag 정책이 다름
    """

    def __init__(
        self,
        evaluator: Optional[ExprEvaluator] = None,
    ) -> None:
        self.evaluator = evaluator or ExprEvaluator()
        self._frame_seq = count(1)
        self._claim_seq = count(1)

    def run(
        self,
        spec: ProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        tokens_by_fragment = self._index_tokens(artifacts.tokens)

        new_frames: list[PartialFrameArtifact] = []
        new_claims: list[ClaimArtifact] = []

        for fragment in artifacts.fragments:
            frag_kind = self._fragment_kind(fragment)

            for parser_spec in spec.parsers.values():
                if frag_kind not in parser_spec.source_selectors:
                    continue

                frame = PartialFrameArtifact(
                    frame_id=f"FRM-{next(self._frame_seq):07d}",
                    parser_name=parser_spec.name,
                    frame_type=parser_spec.build_frame,
                    fragment_ids=[getattr(fragment, "fragment_id", "FRG-UNKNOWN")],
                    slots={},
                )

                ctx = self._build_eval_context(fragment, env, frame)

                for action in parser_spec.actions:
                    # build action은 lowering에서 이미 parser_spec.build_frame으로 올라감
                    if isinstance(action, BindStmt):
                        claims = self._resolve_source_to_claims(
                            source_expr=action.source_expr,
                            fragment=fragment,
                            tokens_by_fragment=tokens_by_fragment,
                            ctx=ctx,
                            parser_name=parser_spec.name,
                            frame_id=frame.frame_id,
                            role_name=action.role_name,
                            extraction_mode_override="explicit",
                        )
                        self._apply_role_binding(
                            frame=frame,
                            role_name=action.role_name,
                            claims=claims,
                            claims_out=new_claims,
                            optional=action.optional,
                            missing_tag_if_empty="missing_parser_failed",
                        )

                    elif isinstance(action, ParserInheritStmt):
                        if action.condition is not None:
                            cond_ok = self.evaluator.eval_bool(action.condition, ctx)
                            if not cond_ok:
                                continue

                        claims = self._resolve_source_to_claims(
                            source_expr=action.source_expr,
                            fragment=fragment,
                            tokens_by_fragment=tokens_by_fragment,
                            ctx=ctx,
                            parser_name=parser_spec.name,
                            frame_id=frame.frame_id,
                            role_name=action.role_name,
                            extraction_mode_override="inherited",
                        )
                        self._apply_role_binding(
                            frame=frame,
                            role_name=action.role_name,
                            claims=claims,
                            claims_out=new_claims,
                            optional=True,
                            missing_tag_if_empty="missing_waiting_context",
                        )

                    elif isinstance(action, TagStmt):
                        claims = self._resolve_source_to_claims(
                            source_expr=action.source_expr,
                            fragment=fragment,
                            tokens_by_fragment=tokens_by_fragment,
                            ctx=ctx,
                            parser_name=parser_spec.name,
                            frame_id=frame.frame_id,
                            role_name=action.role_name,
                            extraction_mode_override="explicit",
                        )
                        self._apply_role_binding(
                            frame=frame,
                            role_name=action.role_name,
                            claims=claims,
                            claims_out=new_claims,
                            optional=True,
                            missing_tag_if_empty=None,
                        )

                    # frame이 갱신되었으니 ctx.frame도 최신 상태 유지
                    ctx.frame = frame

                new_frames.append(frame)

        artifacts.claims.extend(new_claims)
        artifacts.frames.extend(new_frames)
        return artifacts

    # ------------------------------------------------------------------
    # Token indexing
    # ------------------------------------------------------------------

    def _index_tokens(
        self,
        tokens: list[TokenOccurrence],
    ) -> dict[str, dict[str, list[TokenOccurrence]]]:
        out: dict[str, dict[str, list[TokenOccurrence]]] = {}

        for tok in tokens:
            out.setdefault(tok.fragment_id, {}).setdefault(tok.token_name, []).append(tok)

        for frag_map in out.values():
            for token_name, bucket in frag_map.items():
                bucket.sort(key=lambda t: (-t.confidence, t.rank))
        return out

    # ------------------------------------------------------------------
    # Source resolution
    # ------------------------------------------------------------------

    def _resolve_source_to_claims(
        self,
        *,
        source_expr: Expr,
        fragment: Any,
        tokens_by_fragment: dict[str, dict[str, list[TokenOccurrence]]],
        ctx: EvalContext,
        parser_name: str,
        frame_id: str,
        role_name: str,
        extraction_mode_override: Optional[str] = None,
    ) -> list[ClaimArtifact]:
        """
        parser 단계 source expression은 left-biased fallback semantics.
        """
        candidates = self._resolve_source_expr(
            source_expr=source_expr,
            fragment=fragment,
            tokens_by_fragment=tokens_by_fragment,
            ctx=ctx,
        )

        claims: list[ClaimArtifact] = []
        fragment_id = getattr(fragment, "fragment_id", "FRG-UNKNOWN")

        for idx, cand in enumerate(candidates, start=1):
            candidate_state = "active" if idx == 1 else "shadow"

            claim = ClaimArtifact(
                claim_id=f"CLM-{next(self._claim_seq):07d}",
                frame_id=frame_id,
                fragment_id=fragment_id,
                parser_name=parser_name,
                role_name=role_name,
                value=cand.value,
                extraction_mode=extraction_mode_override or cand.extraction_mode,
                confidence=float(cand.confidence),
                candidate_state=candidate_state,
                source_token_id=cand.source_token_id,
                source_fragment_id=cand.source_fragment_id or fragment_id,
                span=cand.span,
                metadata=dict(cand.metadata),
            )
            claims.append(claim)

        return claims

    def _resolve_source_expr(
        self,
        *,
        source_expr: Expr,
        fragment: Any,
        tokens_by_fragment: dict[str, dict[str, list[TokenOccurrence]]],
        ctx: EvalContext,
    ) -> list[SourceCandidate]:
        # parser source에서 a | b | c 는 왼쪽부터 첫 성공 branch를 고름
        if isinstance(source_expr, AlternationExpr):
            for option in source_expr.options:
                out = self._resolve_source_expr(
                    source_expr=option,
                    fragment=fragment,
                    tokens_by_fragment=tokens_by_fragment,
                    ctx=ctx,
                )
                if out:
                    return out
            return []

        # 1) token ref: ActivityToken, SiteToken ...
        if isinstance(source_expr, NameExpr):
            return self._resolve_from_token_name(
                token_name=source_expr.name,
                fragment=fragment,
                tokens_by_fragment=tokens_by_fragment,
            )

        # 2) column(...)
        if isinstance(source_expr, ColumnRefExpr):
            row = getattr(fragment, "metadata", {}).get("row", {}) or {}
            value = row.get(source_expr.column_name)
            if value in (None, ""):
                return []
            return [
                SourceCandidate(
                    value=value,
                    confidence=0.95,
                    extraction_mode="explicit",
                    source_fragment_id=getattr(fragment, "fragment_id", "FRG-UNKNOWN"),
                    span=None,
                    metadata={
                        "source_kind": "column",
                        "column_name": source_expr.column_name,
                    },
                )
            ]

        # 3) context.role
        if isinstance(source_expr, ContextRefExpr):
            resolutions = ctx.env.context_store.resolve_all(
                source_expr.role_name,
                ctx.scope_path,
                column_key=ctx.column_key,
            )
            out: list[SourceCandidate] = []
            for entry in resolutions:
                out.append(
                    SourceCandidate(
                        value=entry.value,
                        confidence=float(entry.confidence),
                        extraction_mode="inherited",
                        source_fragment_id=entry.source_fragment_id,
                        span=None,
                        metadata={
                            "source_kind": "context",
                            "context_id": entry.context_id,
                            "operation": entry.operation,
                            "precedence": entry.precedence,
                        },
                    )
                )
            return out

        # 4) row_label("총")
        if isinstance(source_expr, RowLabelRefExpr):
            row_label = getattr(fragment, "metadata", {}).get("row_label")
            if row_label is None:
                return []
            if source_expr.label in str(row_label):
                return [
                    SourceCandidate(
                        value=source_expr.label,
                        confidence=0.92,
                        extraction_mode="explicit",
                        source_fragment_id=getattr(fragment, "fragment_id", "FRG-UNKNOWN"),
                        metadata={
                            "source_kind": "row_label",
                            "row_label": row_label,
                        },
                    )
                ]
            return []

        # 5) generic expr evaluation fallback
        value = self.evaluator.eval_source(source_expr, ctx)
        return self._coerce_generic_value_to_candidates(
            value,
            fragment_id=getattr(fragment, "fragment_id", "FRG-UNKNOWN"),
        )

    def _resolve_from_token_name(
        self,
        *,
        token_name: str,
        fragment: Any,
        tokens_by_fragment: dict[str, dict[str, list[TokenOccurrence]]],
    ) -> list[SourceCandidate]:
        fragment_id = getattr(fragment, "fragment_id", "FRG-UNKNOWN")
        token_bucket = tokens_by_fragment.get(fragment_id, {}).get(token_name, [])

        out: list[SourceCandidate] = []
        for tok in token_bucket:
            out.append(
                SourceCandidate(
                    value=tok.value,
                    confidence=tok.confidence,
                    extraction_mode="explicit",
                    source_token_id=tok.token_id,
                    source_fragment_id=tok.fragment_id,
                    span=(tok.start, tok.end) if tok.start is not None and tok.end is not None else None,
                    metadata={
                        "source_kind": "token",
                        "token_name": tok.token_name,
                        "source_channel": tok.source_channel,
                        "rank": tok.rank,
                    },
                )
            )
        return out

    def _coerce_generic_value_to_candidates(
        self,
        value: Any,
        *,
        fragment_id: str,
    ) -> list[SourceCandidate]:
        if value is None:
            return []

        if isinstance(value, list):
            out: list[SourceCandidate] = []
            for item in value:
                out.extend(self._coerce_generic_value_to_candidates(item, fragment_id=fragment_id))
            return out

        return [
            SourceCandidate(
                value=value,
                confidence=0.70,
                extraction_mode="derived",
                source_fragment_id=fragment_id,
                metadata={"source_kind": "generic_expr"},
            )
        ]

    # ------------------------------------------------------------------
    # Role binding
    # ------------------------------------------------------------------

    def _apply_role_binding(
        self,
        *,
        frame: PartialFrameArtifact,
        role_name: str,
        claims: list[ClaimArtifact],
        claims_out: list[ClaimArtifact],
        optional: bool,
        missing_tag_if_empty: Optional[str],
    ) -> None:
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

        # 기존 active가 없으면 첫 후보를 active로, 나머지는 shadow로
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

        # 이미 active가 있으면 새 후보는 전부 shadow
        for c in claims:
            c.candidate_state = "shadow"
            slot.shadow_claim_ids.append(c.claim_id)

        claims_out.extend(claims)

    # ------------------------------------------------------------------
    # Context for evaluator
    # ------------------------------------------------------------------

    def _build_eval_context(
        self,
        fragment: Any,
        env: RuntimeEnv,
        frame: PartialFrameArtifact,
    ) -> EvalContext:
        metadata = getattr(fragment, "metadata", {}) or {}
        row = metadata.get("row", {}) if isinstance(metadata, dict) else {}
        row_label = metadata.get("row_label") if isinstance(metadata, dict) else None
        column_key = metadata.get("column_key") if isinstance(metadata, dict) else None

        return EvalContext(
            env=env,
            text=getattr(fragment, "text", ""),
            scope_path=getattr(fragment, "scope_path", tuple()),
            row=row,
            row_label=row_label,
            column_key=column_key,
            frame=frame,
            claims_by_id={},
            local_vars={},
        )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def _fragment_kind(self, fragment: Any) -> str:
        value = getattr(fragment, "fragment_type", None)
        return getattr(value, "value", value)