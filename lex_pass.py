# lex_pass.py
from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from artifacts import CompileArtifacts, TokenOccurrence
from ast_nodes import AlternationExpr, Expr
from expr_eval import EvalContext, ExprEvaluator
from runtime_env import LexCandidate, RuntimeEnv
from spec_nodes import ProgramSpec, TokenSpec


@dataclass
class LexPassConfig:
    # primary hit가 너무 약하거나 모호하면 fallback(LLM)까지 호출
    min_primary_confidence: float = 0.80
    ambiguity_delta: float = 0.05

    # token 하나당 fragment에서 너무 많은 후보를 남기지 않도록 자름
    max_hits_per_token_per_fragment: int = 8

    # fallback hit는 기본적으로 primary보다 보수적으로 다룸
    fallback_confidence_multiplier: float = 0.90


class LexPass:
    """
    fragment -> token occurrences

    설계 원칙:
    1) deterministic(primary) lexer 먼저
    2) 필요할 때만 fallback lexer(LLM) 호출
    3) token expr의 AlternationExpr는 "left-biased fallback"이 아니라
       "candidate union"으로 처리
    4) 이 단계에서는 role-claim으로 확정하지 않고 token occurrence만 뽑음
    """

    def __init__(
        self,
        evaluator: Optional[ExprEvaluator] = None,
        config: Optional[LexPassConfig] = None,
    ) -> None:
        self.evaluator = evaluator or ExprEvaluator()
        self.config = config or LexPassConfig()
        self._seq = count(1)

    def run(
        self,
        spec: ProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        out_tokens: list[TokenOccurrence] = []

        for fragment in artifacts.fragments:
            ctx = self._build_eval_context(fragment, env)

            for token_spec in spec.tokens.values():
                token_hits = self._lex_one_token(token_spec, ctx)
                out_tokens.extend(
                    self._to_occurrences(
                        token_name=token_spec.name,
                        fragment=fragment,
                        hits=token_hits,
                    )
                )

        artifacts.tokens.extend(out_tokens)
        return artifacts

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _lex_one_token(
        self,
        token_spec: TokenSpec,
        ctx: EvalContext,
    ) -> list[LexCandidate]:
        primary_hits = self._eval_token_expr(token_spec.primary_expr, ctx)
        primary_hits = self._postprocess_hits(primary_hits, source_channel="primary")

        fallback_hits: list[LexCandidate] = []
        if token_spec.fallback_expr is not None and self._should_use_fallback(primary_hits):
            fallback_hits = self._eval_token_expr(token_spec.fallback_expr, ctx)
            fallback_hits = self._postprocess_hits(fallback_hits, source_channel="fallback")

        merged = self._merge_hits(primary_hits, fallback_hits)
        merged.sort(
            key=lambda h: (
                -float(h.confidence),
                h.start if h.start is not None else 10**9,
                -((h.end or 0) - (h.start or 0)),
            )
        )
        return merged[: self.config.max_hits_per_token_per_fragment]

    def _eval_token_expr(
        self,
        expr: Expr | None,
        ctx: EvalContext,
    ) -> list[LexCandidate]:
        if expr is None:
            return []

        # token declaration에서 alternation은 union semantics
        if isinstance(expr, AlternationExpr):
            hits: list[LexCandidate] = []
            for option in expr.options:
                hits.extend(self._eval_token_expr(option, ctx))
            return self._merge_hits(hits, [])

        # 나머지는 evaluator에 맡기고 LexCandidate 리스트로 정규화
        value = self.evaluator.eval(expr, ctx)
        return self._coerce_to_lex_candidates(value)

    # ------------------------------------------------------------------
    # Candidate normalization
    # ------------------------------------------------------------------

    def _coerce_to_lex_candidates(self, value: Any) -> list[LexCandidate]:
        if value is None:
            return []

        if isinstance(value, LexCandidate):
            return [value]

        if isinstance(value, list):
            out: list[LexCandidate] = []
            for item in value:
                out.extend(self._coerce_to_lex_candidates(item))
            return out

        if isinstance(value, tuple) and len(value) == 3:
            # convenience: (value, start, end)
            return [
                LexCandidate(
                    value=value[0],
                    start=value[1],
                    end=value[2],
                    confidence=0.80,
                )
            ]

        # scalar는 매우 약한 후보로 래핑
        return [
            LexCandidate(
                value=value,
                start=None,
                end=None,
                confidence=0.50,
            )
        ]

    def _postprocess_hits(
        self,
        hits: list[LexCandidate],
        *,
        source_channel: str,
    ) -> list[LexCandidate]:
        out: list[LexCandidate] = []

        for h in hits:
            conf = float(h.confidence)

            if source_channel == "fallback":
                conf *= self.config.fallback_confidence_multiplier

            meta = dict(h.metadata)
            meta["source_channel"] = source_channel

            out.append(
                LexCandidate(
                    value=h.value,
                    start=h.start,
                    end=h.end,
                    confidence=conf,
                    metadata=meta,
                )
            )

        return out

    def _merge_hits(
        self,
        primary_hits: list[LexCandidate],
        fallback_hits: list[LexCandidate],
    ) -> list[LexCandidate]:
        """
        동일 value/span 후보는 confidence가 높은 쪽을 남긴다.
        """
        by_key: dict[tuple[Any, Optional[int], Optional[int]], LexCandidate] = {}

        for h in [*primary_hits, *fallback_hits]:
            key = (h.value, h.start, h.end)
            prev = by_key.get(key)
            if prev is None or h.confidence > prev.confidence:
                by_key[key] = h

        return list(by_key.values())

    def _should_use_fallback(self, primary_hits: list[LexCandidate]) -> bool:
        if not primary_hits:
            return True

        best = primary_hits[0]
        if best.confidence < self.config.min_primary_confidence:
            return True

        if len(primary_hits) >= 2:
            gap = abs(primary_hits[0].confidence - primary_hits[1].confidence)
            if gap < self.config.ambiguity_delta:
                return True

        return False

    # ------------------------------------------------------------------
    # Materialization
    # ------------------------------------------------------------------

    def _to_occurrences(
        self,
        *,
        token_name: str,
        fragment: Any,
        hits: list[LexCandidate],
    ) -> list[TokenOccurrence]:
        out: list[TokenOccurrence] = []

        fragment_id = getattr(fragment, "fragment_id", "FRG-UNKNOWN")
        text = getattr(fragment, "text", "")

        for rank, hit in enumerate(hits, start=1):
            used_llm = hit.metadata.get("source_channel") == "fallback"

            surface = None
            if (
                hit.start is not None
                and hit.end is not None
                and 0 <= hit.start < hit.end <= len(text)
            ):
                surface = text[hit.start:hit.end]

            metadata = dict(hit.metadata)
            if surface is not None:
                metadata.setdefault("surface", surface)

            out.append(
                TokenOccurrence(
                    token_id=f"TOK-{next(self._seq):07d}",
                    token_name=token_name,
                    fragment_id=fragment_id,
                    value=hit.value,
                    start=hit.start,
                    end=hit.end,
                    confidence=hit.confidence,
                    source_channel=hit.metadata.get("source_channel", "primary"),
                    used_llm=used_llm,
                    rank=rank,
                    metadata=metadata,
                )
            )

        return out

    # ------------------------------------------------------------------
    # Eval context
    # ------------------------------------------------------------------

    def _build_eval_context(self, fragment: Any, env: RuntimeEnv) -> EvalContext:
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
            frame=None,
            claims_by_id={},
            local_vars={},
        )