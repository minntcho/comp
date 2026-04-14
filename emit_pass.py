# emit_pass.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from artifacts import (
    CanonicalRowArtifact,
    ClaimArtifact,
    CompileArtifacts,
    LineageEvidenceArtifact,
    PartialFrameArtifact,
    RoleLineageArtifact,
)
from runtime_env import RuntimeEnv


@dataclass
class EmitPassConfig:
    """
    emit은 committed frame만 대상으로 한다.
    governance에서 merged 여부를 다루므로 여기선 status 변경 안 함.
    """
    emit_only_committed: bool = True
    skip_empty_rows: bool = True
    include_shadow_as_contradiction: bool = True


class EmitPass:
    def __init__(self, config: Optional[EmitPassConfig] = None) -> None:
        self.config = config or EmitPassConfig()

    def run(
        self,
        spec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        claims_by_id = {c.claim_id: c for c in artifacts.claims}

        new_rows: list[CanonicalRowArtifact] = []

        for frame in artifacts.frames:
            if self.config.emit_only_committed and frame.status != "committed":
                continue

            row = self._emit_row(
                frame=frame,
                claims_by_id=claims_by_id,
                env=env,
            )

            if row is None:
                continue

            new_rows.append(row)

        # emit pass는 항상 rows를 재생성하는 게 안전하다
        artifacts.rows = new_rows
        return artifacts

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _emit_row(
        self,
        *,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
        env: RuntimeEnv,
    ) -> Optional[CanonicalRowArtifact]:
        values = self._extract_active_values(frame, claims_by_id)

        site_id = self._resolve_site_id(values.get("site"), env)
        entity_id = self._resolve_entity_id(site_id, env)
        activity_type = self._as_str(values.get("activity_type"))
        period = self._as_str(values.get("period"))
        raw_unit = self._as_str(values.get("raw_unit"))
        raw_amount = self._as_float(values.get("raw_amount"))

        standardized_amount, standardized_unit = self._normalize_amount_and_unit(
            raw_amount=raw_amount,
            raw_unit=raw_unit,
            env=env,
        )

        scope_category = None
        if activity_type and activity_type in env.activity_index:
            scope_category = env.activity_index[activity_type].scope_category

        lineage = self._build_lineage(frame, claims_by_id)

        warning_codes = sorted(
            {
                d.get("code")
                for d in frame.diagnostics
                if isinstance(d, dict) and d.get("severity") == "warning" and d.get("code")
            }
        )
        error_codes = sorted(
            {
                d.get("code")
                for d in frame.diagnostics
                if isinstance(d, dict) and d.get("severity") == "error" and d.get("code")
            }
        )

        if self.config.skip_empty_rows:
            all_core_empty = (
                site_id is None
                and period is None
                and activity_type is None
                and raw_amount is None
                and raw_unit is None
            )
            if all_core_empty:
                return None

        row = CanonicalRowArtifact(
            row_id=self._row_id_from_frame(frame.frame_id),
            frame_id=frame.frame_id,
            parser_name=frame.parser_name,
            frame_type=frame.frame_type,
            status=frame.status,

            site_id=site_id,
            entity_id=entity_id,
            period=period,
            activity_type=activity_type,

            raw_amount=raw_amount,
            raw_unit=raw_unit,
            standardized_amount=standardized_amount,
            standardized_unit=standardized_unit,

            scope_category=scope_category,
            resolution_score=float(frame.resolution_score),
            lineage=lineage,

            source_fragment_ids=list(frame.fragment_ids),
            warning_codes=warning_codes,
            error_codes=error_codes,

            metadata={
                "iteration_count": frame.iteration_count,
                "stable_count": frame.stable_count,
                "termination_reason": frame.termination_reason,
                "repair_trace_len": len(frame.metadata.get("repair_trace", [])),
            },
        )
        return row

    # ------------------------------------------------------------------
    # Value extraction
    # ------------------------------------------------------------------

    def _extract_active_values(
        self,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}

        for role_name, slot in frame.slots.items():
            if not slot.active_claim_id:
                continue
            claim = claims_by_id.get(slot.active_claim_id)
            if claim is None:
                continue
            out[role_name] = claim.value

        return out

    # ------------------------------------------------------------------
    # Lineage
    # ------------------------------------------------------------------

    def _build_lineage(
        self,
        frame: PartialFrameArtifact,
        claims_by_id: dict[str, ClaimArtifact],
    ) -> dict[str, RoleLineageArtifact]:
        lineage: dict[str, RoleLineageArtifact] = {}

        for role_name, slot in frame.slots.items():
            node = RoleLineageArtifact()

            # active claim
            if slot.active_claim_id and slot.active_claim_id in claims_by_id:
                active = claims_by_id[slot.active_claim_id]
                evidence = self._to_lineage_evidence(active)

                if active.extraction_mode == "explicit":
                    node.direct.append(evidence)
                elif active.extraction_mode == "inherited":
                    node.inherited.append(evidence)
                elif active.extraction_mode == "backward_inferred":
                    node.backward_inferred.append(evidence)
                else:
                    node.derived.append(evidence)

            # shadow / rejected claims = contradicted_by 관점으로 남김
            if self.config.include_shadow_as_contradiction:
                for cid in [*slot.shadow_claim_ids, *slot.rejected_claim_ids]:
                    claim = claims_by_id.get(cid)
                    if claim is None:
                        continue
                    node.contradicted_by.append(self._to_lineage_evidence(claim))

            lineage[role_name] = node

        return lineage

    def _to_lineage_evidence(self, claim: ClaimArtifact) -> LineageEvidenceArtifact:
        return LineageEvidenceArtifact(
            claim_id=claim.claim_id,
            fragment_id=claim.source_fragment_id or claim.fragment_id,
            span=claim.span,
            extraction_mode=claim.extraction_mode,
            value=claim.value,
            reason_codes=list(claim.reason_codes),
            evidence_ids=list(claim.evidence_ids),
            metadata=dict(claim.metadata),
        )

    # ------------------------------------------------------------------
    # Canonicalization helpers
    # ------------------------------------------------------------------

    def _resolve_site_id(self, value: Any, env: RuntimeEnv) -> Optional[str]:
        if value in (None, ""):
            return None

        # 이미 site_id일 수 있음
        if isinstance(value, str) and value in env.site_records:
            return value

        # alias lookup
        key = str(value).strip().lower()
        return env.site_alias_index.get(key)

    def _resolve_entity_id(self, site_id: Optional[str], env: RuntimeEnv) -> Optional[str]:
        if site_id is None:
            return None
        rec = env.site_records.get(site_id)
        if rec is None:
            return None
        return rec.entity_id

    def _normalize_amount_and_unit(
        self,
        *,
        raw_amount: Optional[float],
        raw_unit: Optional[str],
        env: RuntimeEnv,
    ) -> tuple[Optional[float], Optional[str]]:
        if raw_amount is None or raw_unit is None:
            return None, None

        spec = env.unit_index.get(raw_unit)
        if spec is None or spec.normalize_to is None or spec.normalize_op is None or spec.normalize_factor is None:
            return raw_amount, raw_unit

        x = raw_amount
        factor = float(spec.normalize_factor)

        if spec.normalize_op == "*":
            x = x * factor
        elif spec.normalize_op == "/":
            x = x / factor
        elif spec.normalize_op == "+":
            x = x + factor
        elif spec.normalize_op == "-":
            x = x - factor

        return float(x), spec.normalize_to

    def _as_float(self, value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        if isinstance(value, (int, float)):
            return float(value)

        try:
            return float(str(value).replace(",", "").strip())
        except Exception:
            return None

    def _as_str(self, value: Any) -> Optional[str]:
        if value in (None, ""):
            return None
        return str(value)

    def _row_id_from_frame(self, frame_id: str) -> str:
        # e.g. FRM-0000001 -> ROW-0000001
        if frame_id.startswith("FRM-"):
            return "ROW-" + frame_id[len("FRM-"):]
        return f"ROW-{frame_id}"