from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterable

if TYPE_CHECKING:
    from comp.scenarios.synthetic.generator import SyntheticRun


def write_synthetic_run(run: SyntheticRun, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "master").mkdir(exist_ok=True)
    (run_dir / "raw_sources").mkdir(exist_ok=True)
    if run.resolution_artifacts.unit_witnesses:
        (run_dir / "resolution_artifacts").mkdir(exist_ok=True)
    (run_dir / "oracle").mkdir(exist_ok=True)

    _write_json(run_dir / "manifest.json", run.manifest)
    _write_csv(
        run_dir / "master" / "reference_catalog.csv",
        [
            "reference_id",
            "reference_type",
            "label",
            "geography",
            "valid_period",
            "method",
            "factor_value",
            "input_unit",
            "output_unit",
            "source",
            "witness_id",
        ],
        (record.to_row() for record in run.master.reference_catalog),
    )
    _write_csv(
        run_dir / "master" / "sites.csv",
        ["site_id", "site_name", "geography"],
        run.master.sites,
    )
    _write_csv(
        run_dir / "master" / "products.csv",
        ["product_id", "site_id"],
        run.master.products,
    )
    _write_csv(
        run_dir / "raw_sources" / "erp_electricity.csv",
        [
            "source_row_id",
            "source_ref",
            "period",
            "site_id",
            "site_name",
            "product_id",
            "activity_type",
            "amount",
            "unit",
        ],
        (row.to_row() for row in run.raw_sources.electricity_rows),
    )
    if run.resolution_artifacts.unit_witnesses:
        _write_csv(
            run_dir / "resolution_artifacts" / "unit_witnesses.csv",
            [
                "artifact_id",
                "obligation_id",
                "source_row_id",
                "field",
                "resolved_value",
                "witness_id",
                "source_ref",
                "rationale",
            ],
            (
                artifact.to_row()
                for artifact in run.resolution_artifacts.unit_witnesses
            ),
        )
    _write_csv(
        run_dir / "oracle" / "expected_claims.csv",
        ["claim_id", "field", "value", "unit", "witness_id", "source_row_id"],
        (claim.to_row() for claim in run.oracle.expected_claims),
    )
    _write_csv(
        run_dir / "oracle" / "expected_derived_claims.csv",
        ["claim_id", "field", "value", "unit", "formula_id"],
        (claim.to_row() for claim in run.oracle.expected_derived_claims),
    )
    _write_csv(
        run_dir / "oracle" / "expected_obligations.csv",
        ["obligation_id", "kind", "field", "reason"],
        (obligation.to_row() for obligation in run.oracle.expected_obligations),
    )
    _write_csv(
        run_dir / "oracle" / "expected_hazards.csv",
        ["hazard_id", "kind", "field", "severity"],
        (hazard.to_row() for hazard in run.oracle.expected_hazards),
    )
    _write_csv(
        run_dir / "oracle" / "expected_failed_claims.csv",
        ["failed_claim_id", "field", "value", "reason", "source_row_id"],
        (claim.to_row() for claim in run.oracle.expected_failed_claims),
    )
    _write_csv(
        run_dir / "oracle" / "injected_anomalies.csv",
        ["anomaly_id", "anomaly_type", "source_row_id", "field", "description"],
        (anomaly.to_row() for anomaly in run.oracle.injected_anomalies),
    )
    _write_csv(
        run_dir / "oracle" / "source_to_expected_claim_map.csv",
        [
            "source_ref",
            "source_row_id",
            "expected_claim_id",
            "expected_field",
            "witness_id",
        ],
        (item.to_row() for item in run.oracle.source_to_expected_claim_map),
    )
    if run.oracle.expected_resolved_obligations is not None:
        _write_csv(
            run_dir / "oracle" / "expected_resolved_obligations.csv",
            ["obligation_id", "kind", "field", "reason"],
            (
                obligation.to_row()
                for obligation in run.oracle.expected_resolved_obligations
            ),
        )
    if run.oracle.expected_resolution_artifacts is not None:
        _write_csv(
            run_dir / "oracle" / "expected_resolution_artifacts.csv",
            [
                "artifact_id",
                "obligation_id",
                "source_row_id",
                "field",
                "resolved_value",
                "witness_id",
                "source_ref",
            ],
            (
                artifact.to_row()
                for artifact in run.oracle.expected_resolution_artifacts
            ),
        )
    if run.oracle.expected_receipt is not None:
        _write_json(
            run_dir / "oracle" / "expected_receipt.json",
            run.oracle.expected_receipt.to_payload(),
        )
    return run_dir


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_csv(
    path: Path,
    headers: list[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


__all__ = ["write_synthetic_run"]
