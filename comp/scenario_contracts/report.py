from __future__ import annotations

import json
from pathlib import Path

from comp.scenario_contracts.result import ScenarioResult


def write_report(result: ScenarioResult, path: str | Path) -> Path:
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(result.to_dict(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return report_path


__all__ = ["write_report"]
