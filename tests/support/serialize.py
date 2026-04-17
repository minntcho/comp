from __future__ import annotations

from typing import Any

from artifacts import CompileArtifacts, DiagnosticArtifact


def project_result(result: Any) -> dict[str, Any]:
    return project_artifacts(result.artifacts)


def project_artifacts(artifacts: CompileArtifacts) -> dict[str, Any]:
    return {
        "frames": [
            {
                "parser_name": f.parser_name,
                "frame_type": f.frame_type,
                "status": f.status,
                "diagnostic_codes": _diagnostic_codes(f.diagnostics),
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


def _diagnostic_codes(diagnostics: list[DiagnosticArtifact]) -> list[str]:
    codes: list[str] = []
    for diag in diagnostics:
        if not isinstance(diag, DiagnosticArtifact):
            raise TypeError("frame.diagnostics must contain DiagnosticArtifact only")
        if diag.severity and diag.code:
            codes.append(f"{diag.severity}:{diag.code}")
    return sorted(codes)
