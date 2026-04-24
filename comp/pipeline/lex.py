from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from comp.artifacts import CompileArtifacts, TokenOccurrence
from comp.dsl.compiled_spec import CompiledProgramSpec
from comp.eval.lex import LexEvaluator
from comp.runtime_env import LexCandidate, RuntimeEnv


@dataclass
class LexPassConfig:
    min_primary_confidence: float = 0.80
    ambiguity_delta: float = 0.05
    max_hits_per_token_per_fragment: int = 8
    fallback_confidence_multiplier: float = 0.90


class LexPass:
    """
    fragment -> token occurrences

    설계 원칙:
    1) deterministic(primary) lexer 먼저
    2) 필요할 때만 fallback lexer(LLM) 호출
    3) token declaration의 alternation은 union semantics
    4) 이 단계에서는 role-claim으로 확정하지 않고 token occurrence만 뽑음
    """

    def __init__(
        self,
        evaluator: Optional[LexEvaluator] = None,
        config: Optional[LexPassConfig] = None,
    ) -> None:
        self.evaluator = evaluator or LexEvaluator()
        self.config = config or LexPassConfig()
        self._seq = count(1)

    def run(
        self,
        spec: CompiledProgramSpec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        if not isinstance(spec, CompiledProgramSpec):
            raise TypeError("LexPass requires CompiledProgramSpec")

        out_tokens: list[TokenOccurrence] = []

        for fragment in artifacts.fragments:
            ctx = self._build_eval_context(fragment, env)

            for token_spec in spec.compiled_tokens.values():
                token_hits = self._lex_one_token(token_spec, ctx)
                out_tokens.extend(
                    self._to_occurrences(
                        token_name=token_spec.syntax.name,
                        fragment=fragment,
                        hits=token_hits,
                    )
                )

        artifacts.tokens.extend(out_tokens)
        return artifacts

    def _lex_one_token(
        self,
        token_spec,
        ctx,
    ) -> list[LexCandidate]:
        primary_hits = self.evaluator.resolve(token_spec.primary_ir, ctx)
        primary_hits = self._postprocess_hits(primary_hits, source_channel="primary")

        fallback_hits: list[LexCandidate] = []
        if token_spec.fallback_ir is not None and self._should_use_fallback(primary_hits):
            fallback_hits = self.evaluator.resolve(token_spec.fallback_ir, ctx)
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

    def _build_eval_context(self, fragment: Any, env: RuntimeEnv):
        from comp.eval.expr import EvalContext

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


__all__ = ["LexPassConfig", "LexPass"]
