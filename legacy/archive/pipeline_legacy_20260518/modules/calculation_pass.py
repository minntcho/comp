# calculation_pass.py
from __future__ import annotations

from dataclasses import dataclass
from itertools import count
from typing import Any, Optional

from artifacts import CalculationArtifact, CanonicalRowArtifact, CompileArtifacts
from runtime_env import RuntimeEnv


@dataclass
class CalculationPassConfig:
    """
    기본 원칙:
    - merged row만 계산
    - ActivityObservation만 계산
    - standardized_amount/unit 우선 사용
    - 필요하면 raw_amount/raw_unit fallback 허용
    """
    calculate_only_merged: bool = True
    supported_frame_types: tuple[str, ...] = ("ActivityObservation",)
    allow_raw_fallback: bool = True

    # governance가 막아줬겠지만 마지막 safety belt
    exclude_rows_with_errors: bool = True
    exclude_rows_with_aggregate_warning: bool = True

    emit_events: bool = True
    replace_existing_calculations: bool = True


class CalculationPass:
    def __init__(self, config: Optional[CalculationPassConfig] = None) -> None:
        self.config = config or CalculationPassConfig()
        self._calc_seq = count(1)

    def run(
        self,
        spec,
        artifacts: CompileArtifacts,
        env: RuntimeEnv,
    ) -> CompileArtifacts:
        results: list[CalculationArtifact] = []

        for row in artifacts.rows:
            result = self._calculate_row(row=row, env=env)
            if result is None:
                continue

            results.append(result)

            # row metadata에 간단 trace 남김
            row.metadata.setdefault("calculation_trace", []).append(
                {
                    "calculation_id": result.calculation_id,
                    "status": result.calculation_status,
                    "reason": result.exclusion_reason,
                    "factor_id": result.factor_id,
                    "co2e_kg": result.co2e_kg,
                }
            )

            if self.config.emit_events:
                artifacts.event_log.append(
                    {
                        "event_id": f"EVT-CALC-{result.calculation_id}",
                        "record_id": row.row_id,
                        "event_type": (
                            "CALCULATED"
                            if result.calculation_status == "success"
                            else "CALCULATION_EXCLUDED"
                            if result.calculation_status == "excluded"
                            else "CALCULATION_FAILED"
                        ),
                        "from_status": row.status,
                        "to_status": row.status,
                        "actor": "calculation_engine",
                        "reason_codes": [result.exclusion_reason] if result.exclusion_reason else [],
                        "created_at": result.calculated_at.isoformat() + "Z",
                    }
                )

        if self.config.replace_existing_calculations:
            artifacts.calculations = results
        else:
            artifacts.calculations.extend(results)

        return artifacts

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _calculate_row(
        self,
        *,
        row: CanonicalRowArtifact,
        env: RuntimeEnv,
    ) -> Optional[CalculationArtifact]:
        # 1) merged row만
        if self.config.calculate_only_merged and row.status != "merged":
            return None

        # 2) frame type gate
        if row.frame_type not in self.config.supported_frame_types:
            return self._excluded(
                row=row,
                reason="unsupported_frame_type",
                metadata={"supported_frame_types": list(self.config.supported_frame_types)},
            )

        # 3) aggregate warning이 있으면 마지막 safety belt
        if self.config.exclude_rows_with_aggregate_warning and "AggregateRow" in set(row.warning_codes):
            return self._excluded(
                row=row,
                reason="aggregate_row_excluded",
            )

        # 4) error diagnostics 있으면 계산 금지
        if self.config.exclude_rows_with_errors and row.error_codes:
            return self._excluded(
                row=row,
                reason="row_has_error_diagnostics",
                metadata={"error_codes": list(row.error_codes)},
            )

        # 5) 입력값 선택
        amount, unit, used_raw_fallback = self._pick_amount_unit(row)

        if row.activity_type in (None, ""):
            return self._failed(
                row=row,
                reason="missing_activity_type",
                amount=amount,
                unit=unit,
            )

        if amount is None or unit is None:
            return self._failed(
                row=row,
                reason="missing_amount_or_unit",
                amount=amount,
                unit=unit,
            )

        # 6) factor lookup
        factor = env.factor_index.get((row.activity_type, unit))

        # standardized lookup 실패 시 raw fallback 재시도
        if factor is None and not used_raw_fallback and self.config.allow_raw_fallback:
            if row.raw_amount is not None and row.raw_unit not in (None, ""):
                amount = float(row.raw_amount)
                unit = str(row.raw_unit)
                used_raw_fallback = True
                factor = env.factor_index.get((row.activity_type, unit))

        if factor is None:
            return self._failed(
                row=row,
                reason="factor_not_found",
                amount=amount,
                unit=unit,
                metadata={
                    "factor_lookup_key": [row.activity_type, unit],
                    "used_raw_fallback": used_raw_fallback,
                },
            )

        # 7) factor 적용
        try:
            applied_factor = float(factor["emission_factor"])
        except Exception:
            return self._failed(
                row=row,
                reason="invalid_factor_value",
                amount=amount,
                unit=unit,
                metadata={"factor_row": dict(factor)},
            )

        co2e_kg = float(amount) * applied_factor

        return CalculationArtifact(
            calculation_id=f"CAL-{next(self._calc_seq):07d}",
            row_id=row.row_id,
            frame_id=row.frame_id,

            row_status_at_calc=row.status,
            calculation_status="success",

            activity_type=row.activity_type,

            standardized_amount=float(amount),
            standardized_unit=str(unit),

            factor_id=factor.get("factor_id"),
            applied_factor=applied_factor,
            factor_unit=factor.get("factor_unit"),

            co2e_kg=round(co2e_kg, 6),
            scope_category=row.scope_category,

            metadata={
                "used_raw_fallback": used_raw_fallback,
                "source_row_status": row.status,
                "factor_lookup_key": [row.activity_type, unit],
                "warning_codes": list(row.warning_codes),
                "error_codes": list(row.error_codes),
            },
        )

    # ------------------------------------------------------------------
    # Amount / unit selection
    # ------------------------------------------------------------------

    def _pick_amount_unit(
        self,
        row: CanonicalRowArtifact,
    ) -> tuple[Optional[float], Optional[str], bool]:
        # standardized 우선
        if row.standardized_amount is not None and row.standardized_unit not in (None, ""):
            return float(row.standardized_amount), str(row.standardized_unit), False

        # raw fallback
        if self.config.allow_raw_fallback:
            if row.raw_amount is not None and row.raw_unit not in (None, ""):
                return float(row.raw_amount), str(row.raw_unit), True

        return None, None, False

    # ------------------------------------------------------------------
    # Result constructors
    # ------------------------------------------------------------------

    def _excluded(
        self,
        *,
        row: CanonicalRowArtifact,
        reason: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> CalculationArtifact:
        return CalculationArtifact(
            calculation_id=f"CAL-{next(self._calc_seq):07d}",
            row_id=row.row_id,
            frame_id=row.frame_id,

            row_status_at_calc=row.status,
            calculation_status="excluded",

            activity_type=row.activity_type,
            scope_category=row.scope_category,

            exclusion_reason=reason,
            metadata=metadata or {},
        )

    def _failed(
        self,
        *,
        row: CanonicalRowArtifact,
        reason: str,
        amount: Optional[float],
        unit: Optional[str],
        metadata: Optional[dict[str, Any]] = None,
    ) -> CalculationArtifact:
        return CalculationArtifact(
            calculation_id=f"CAL-{next(self._calc_seq):07d}",
            row_id=row.row_id,
            frame_id=row.frame_id,

            row_status_at_calc=row.status,
            calculation_status="failed",

            activity_type=row.activity_type,
            standardized_amount=amount,
            standardized_unit=unit,
            scope_category=row.scope_category,

            exclusion_reason=reason,
            metadata=metadata or {},
        )