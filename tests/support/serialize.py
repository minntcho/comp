from __future__ import annotations

from typing import Any

from artifacts import CompileArtifacts

# NOTE(PR0): serializer intentionally tolerates mixed diagnostic shapes.
# This is temporary and must be removed in PR1.


def project_result(result: Any) -> dict[str, Any]:
    return project_artifacts(result.artifacts)


def project_artifacts(artifacts: CompileArtifacts) -> dict[str, Any]:
    return {
        "frames": [
            {
                "parser_name": f.parser_name,
                "frame_type": f.frame_type,
                "status": f.status,
                "diagnostic_codes": sorted(
                    [
                        _diag_get(d, "severity") + ":" + _diag_get(d, "code")
                        for d in f.diagnostics
                        if _diag_get(d, "severity") and _diag_get(d, "code")
                    ]
                ),
            }
            for f in artifacts.frames
        ],
        "rows": [
            {
                "frame_type": r.frame_type,
                "status": r.status,
                "site_id": r.site_id,
                "activity_type": r.activity_type,
                "period": r.period,
                "warning_codes": sorted(list(r.warning_codes)),
                "error_codes": sorted(list(r.error_codes)),
            }
            for r in artifacts.rows
        ],
        "merge_log": [
            {
                "action": m.action,
                "from_status": m.from_status,
                "to_status": m.to_status,
                "reason_codes": sorted(list(m.reason_codes)),
            }
            for m in artifacts.merge_log
        ],
        "calculations": [
            {
                "calculation_status": c.calculation_status,
                "exclusion_reason": c.exclusion_reason,
                "activity_type": c.activity_type,
                "co2e_kg": c.co2e_kg,
            }
            for c in artifacts.calculations
        ],
    }


def _diag_get(diag: Any, key: str):
    # TEMP(PR0): compatibility shim for mixed diagnostics representations.
    # Remove in PR1 after frame.diagnostics becomes DiagnosticArtifact-only.
    if isinstance(diag, dict):
        return diag.get(key)
    return getattr(diag, key, None)
