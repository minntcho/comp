from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InvariantResult:
    name: str
    status: str
    message: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "status": self.status,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class ScenarioResult:
    scenario_id: str
    status: str
    artifact_count: int
    receipt_count: int
    public_row_count: int
    replay_checked_count: int
    replay_failed_count: int
    invariant_results: tuple[InvariantResult, ...]
    performance: dict[str, float] = field(default_factory=dict)
    report_path: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "status": self.status,
            "counts": {
                "artifacts": self.artifact_count,
                "receipts": self.receipt_count,
                "public_rows": self.public_row_count,
            },
            "replay": {
                "checked": self.replay_checked_count,
                "failed": self.replay_failed_count,
            },
            "invariants": [
                invariant.to_dict() for invariant in self.invariant_results
            ],
            "performance": self.performance,
        }


__all__ = ["InvariantResult", "ScenarioResult"]
