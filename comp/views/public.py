from __future__ import annotations

from typing import Any, Iterable, Optional

from artifacts import (
    CanonicalRowArtifact,
    ClaimArtifact,
    LineageEvidenceArtifact,
    PartialFrameArtifact,
    RoleLineageArtifact,
    error_codes_from_diagnostics,
    warning_codes_from_diagnostics,
)
from comp.judgment import ProjectionSpec, project_public_row
from runtime_env import RuntimeEnv

DEFAULT_PUBLIC_PROJECTION = ProjectionSpec(
    "canonical_row",
    (
        "site_id",
        "entity_id",
        "period",
        "activity_type",
        "raw_amount",
        "raw_unit",
        "standardized_amount",
        "standardized_unit",
        "scope_category",
    ),
)


def materialize_public_rows(
    frames: Iterable[PartialFrameArtifact],
    claims_by_id: dict[str, ClaimArtifact],
    env: RuntimeEnv,
    *,
    emit_only_committed: bool = True,
    skip_empty_rows: bool = True,
    include_shadow_as_contradiction: bool = True,
) -> list[CanonicalRowArtifact]:
    rows: list[CanonicalRowArtifact] = []
    for frame in frames:
        if emit_only_committed and frame.status != "committed":
            continue
        row = project_canonical_row(
            frame=frame,
            claims_by_id=claims_by_id,
            env=env,
            skip_empty_rows=skip_empty_rows,
            include_shadow_as_contradiction=include_shadow_as_contradiction,
        )
        if row is not None:
            rows.append(row)
    return rows


def project_canonical_row(
    *,
    frame: PartialFrameArtifact,
    claims_by_id: dict[str, ClaimArtifact],
    env: RuntimeEnv,
    projection: ProjectionSpec = DEFAULT_PUBLIC_PROJECTION,
    skip_empty_rows: bool = True,
    include_shadow_as_contradiction: bool = True,
) -> Optional[CanonicalRowArtifact]:
    values = _extract_active_values(frame, claims_by_id)

    site_id = _resolve_site_id(values.get("site"), env)
    entity_id = _resolve_entity_id(site_id, env)
    activity_type = _as_str(values.get("activity_type"))
    period = _as_str(values.get("period"))
    raw_unit = _as_str(values.get("raw_unit"))
    raw_amount = _as_float(values.get("raw_amount"))

    standardized_amount, standardized_unit = _normalize_amount_and_unit(
        raw_amount=raw_amount,
        raw_unit=raw_unit,
        env=env,
    )

    scope_category = None
    if activity_type and activity_type in env.activity_index:
        scope_category = env.activity_index[activity_type].scope_category

    field_values = {
        "site_id": site_id,
        "entity_id": entity_id,
        "period": period,
        "activity_type": activity_type,
        "raw_amount": raw_amount,
        "raw_unit": raw_unit,
        "standardized_amount": standardized_amount,
        "standardized_unit": standardized_unit,
        "scope_category": scope_category,
    }
    projected = project_public_row(field_values, projection)

    lineage = _build_lineage(frame, claims_by_id, include_shadow_as_contradiction=include_shadow_as_contradiction)
    warning_codes = warning_codes_from_diagnostics(frame.diagnostics)
    error_codes = error_codes_from_diagnostics(frame.diagnostics)

    if skip_empty_rows:
        all_core_empty = (
            projected["site_id"] is None
            and projected["period"] is None
            and projected["activity_type"] is None
            and projected["raw_amount"] is None
            and projected["raw_unit"] is None
        )
        if all_core_empty:
            return None

    return CanonicalRowArtifact(
        row_id=_row_id_from_frame(frame.frame_id),
        frame_id=frame.frame_id,
        parser_name=frame.parser_name,
        frame_type=frame.frame_type,
        status=frame.status,
        site_id=projected["site_id"],
        entity_id=projected["entity_id"],
        period=projected["period"],
        activity_type=projected["activity_type"],
        raw_amount=projected["raw_amount"],
        raw_unit=projected["raw_unit"],
        standardized_amount=projected["standardized_amount"],
        standardized_unit=projected["standardized_unit"],
        scope_category=projected["scope_category"],
        resolution_score=float(frame.runtime.resolution_score),
        lineage=lineage,
        source_fragment_ids=list(frame.fragment_ids),
        warning_codes=warning_codes,
        error_codes=error_codes,
        metadata={
            "projection_id": projection.projection_id,
            "iteration_count": frame.runtime.iteration_count,
            "stable_count": frame.runtime.stable_count,
            "termination_reason": frame.runtime.termination_reason,
            "repair_trace_len": len(frame.metadata.get("repair_trace", [])),
            "selection_receipts": list(frame.metadata.get("selection_receipts", [])),
        },
    )


def _extract_active_values(
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


def _build_lineage(
    frame: PartialFrameArtifact,
    claims_by_id: dict[str, ClaimArtifact],
    *,
    include_shadow_as_contradiction: bool,
) -> dict[str, RoleLineageArtifact]:
    lineage: dict[str, RoleLineageArtifact] = {}
    for role_name, slot in frame.slots.items():
        node = RoleLineageArtifact()
        if slot.active_claim_id and slot.active_claim_id in claims_by_id:
            active = claims_by_id[slot.active_claim_id]
            evidence = _to_lineage_evidence(active)
            if active.extraction_mode == "explicit":
                node.direct.append(evidence)
            elif active.extraction_mode == "inherited":
                node.inherited.append(evidence)
            elif active.extraction_mode == "backward_inferred":
                node.backward_inferred.append(evidence)
            else:
                node.derived.append(evidence)
        if include_shadow_as_contradiction:
            for cid in [*slot.shadow_claim_ids, *slot.rejected_claim_ids]:
                claim = claims_by_id.get(cid)
                if claim is None:
                    continue
                node.contradicted_by.append(_to_lineage_evidence(claim))
        lineage[role_name] = node
    return lineage


def _to_lineage_evidence(claim: ClaimArtifact) -> LineageEvidenceArtifact:
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


def _resolve_site_id(value: Any, env: RuntimeEnv) -> Optional[str]:
    if value in (None, ""):
        return None
    if isinstance(value, str) and value in env.site_records:
        return value
    key = str(value).strip().lower()
    return env.site_alias_index.get(key)


def _resolve_entity_id(site_id: Optional[str], env: RuntimeEnv) -> Optional[str]:
    if site_id is None:
        return None
    rec = env.site_records.get(site_id)
    if rec is None:
        return None
    return rec.entity_id


def _normalize_amount_and_unit(
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


def _as_float(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return None


def _as_str(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    return str(value)


def _row_id_from_frame(frame_id: str) -> str:
    if frame_id.startswith("FRM-"):
        return "ROW-" + frame_id[len("FRM-"):]
    return f"ROW-{frame_id}"


__all__ = [
    "DEFAULT_PUBLIC_PROJECTION",
    "project_canonical_row",
    "materialize_public_rows",
]
