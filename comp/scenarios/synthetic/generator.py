from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.manifest import build_manifest


OUTPUT_CONTRACT = ("master", "raw_sources", "oracle")


@dataclass(frozen=True)
class MasterReferenceRecord:
    reference_id: str
    reference_type: str
    label: str
    geography: str
    valid_period: str
    method: str
    factor_value: int | float
    input_unit: str
    output_unit: str
    source: str
    witness_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_type": self.reference_type,
            "label": self.label,
            "geography": self.geography,
            "valid_period": self.valid_period,
            "method": self.method,
            "factor_value": self.factor_value,
            "input_unit": self.input_unit,
            "output_unit": self.output_unit,
            "source": self.source,
            "witness_id": self.witness_id,
        }


@dataclass(frozen=True)
class RawElectricityRow:
    source_row_id: str
    source_ref: str
    period: str
    site_id: str
    site_name: str
    product_id: str
    activity_type: str
    amount: int | float
    unit: str

    def to_row(self) -> dict[str, Any]:
        return {
            "source_row_id": self.source_row_id,
            "period": self.period,
            "site_id": self.site_id,
            "site_name": self.site_name,
            "product_id": self.product_id,
            "activity_type": self.activity_type,
            "amount": self.amount,
            "unit": self.unit,
        }


@dataclass(frozen=True)
class ExpectedClaim:
    claim_id: str
    field: str
    value: int | float | str
    unit: str | None
    witness_id: str
    source_row_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "field": self.field,
            "value": self.value,
            "unit": self.unit or "",
            "witness_id": self.witness_id,
            "source_row_id": self.source_row_id,
        }


@dataclass(frozen=True)
class ExpectedDerivedClaim:
    claim_id: str
    field: str
    value: int | float
    unit: str
    formula_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "field": self.field,
            "value": self.value,
            "unit": self.unit,
            "formula_id": self.formula_id,
        }


@dataclass(frozen=True)
class ExpectedSourceMap:
    source_ref: str
    source_row_id: str
    expected_claim_id: str
    expected_field: str
    witness_id: str

    def to_row(self) -> dict[str, Any]:
        return {
            "source_ref": self.source_ref,
            "source_row_id": self.source_row_id,
            "expected_claim_id": self.expected_claim_id,
            "expected_field": self.expected_field,
            "witness_id": self.witness_id,
        }


@dataclass(frozen=True)
class SyntheticMaster:
    reference_catalog: tuple[MasterReferenceRecord, ...]
    sites: tuple[dict[str, Any], ...]
    products: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class SyntheticRawSources:
    electricity_rows: tuple[RawElectricityRow, ...]


@dataclass(frozen=True)
class SyntheticOracle:
    expected_claims: tuple[ExpectedClaim, ...]
    expected_derived_claims: tuple[ExpectedDerivedClaim, ...]
    expected_obligations: tuple[dict[str, Any], ...]
    expected_hazards: tuple[dict[str, Any], ...]
    source_to_expected_claim_map: tuple[ExpectedSourceMap, ...]


@dataclass(frozen=True)
class SyntheticRun:
    config: SyntheticScenarioConfig
    manifest: dict[str, Any]
    master: SyntheticMaster
    raw_sources: SyntheticRawSources
    oracle: SyntheticOracle
    output_contract: tuple[str, ...] = OUTPUT_CONTRACT


def generate_synthetic_pcf_run(config: SyntheticScenarioConfig) -> SyntheticRun:
    source_witness_id = f"witness:{config.source_row_id}:electricity_kwh"
    derived_value = _multiply(config.electricity_kwh, config.factor_value)
    reference = MasterReferenceRecord(
        reference_id=config.factor_reference_id,
        reference_type="emission_factor",
        label=f"{config.geography} grid electricity factor {config.reporting_period}",
        geography=config.geography,
        valid_period=config.reporting_period,
        method="location_based",
        factor_value=config.factor_value,
        input_unit=config.factor_input_unit,
        output_unit=config.factor_output_unit,
        source="synthetic_reference_catalog",
        witness_id=f"reference-witness:{config.factor_reference_id}",
    )
    raw_row = RawElectricityRow(
        source_row_id=config.source_row_id,
        source_ref=config.source_ref,
        period=config.reporting_period,
        site_id=config.site_id,
        site_name=config.site_name,
        product_id=config.product_id,
        activity_type="electricity",
        amount=config.electricity_kwh,
        unit=config.electricity_unit,
    )
    expected_claim = ExpectedClaim(
        claim_id=config.input_claim_id,
        field="electricity_kwh",
        value=config.electricity_kwh,
        unit=config.electricity_unit,
        witness_id=source_witness_id,
        source_row_id=config.source_row_id,
    )
    return SyntheticRun(
        config=config,
        manifest=build_manifest(config, output_contract=OUTPUT_CONTRACT),
        master=SyntheticMaster(
            reference_catalog=(reference,),
            sites=(
                {
                    "site_id": config.site_id,
                    "site_name": config.site_name,
                    "geography": config.geography,
                },
            ),
            products=(
                {
                    "product_id": config.product_id,
                    "site_id": config.site_id,
                },
            ),
        ),
        raw_sources=SyntheticRawSources(electricity_rows=(raw_row,)),
        oracle=SyntheticOracle(
            expected_claims=(expected_claim,),
            expected_derived_claims=(
                ExpectedDerivedClaim(
                    claim_id=config.output_claim_id,
                    field="co2e_kg",
                    value=derived_value,
                    unit=config.factor_output_unit,
                    formula_id=config.formula_id,
                ),
            ),
            expected_obligations=(),
            expected_hazards=(),
            source_to_expected_claim_map=(
                ExpectedSourceMap(
                    source_ref=config.source_ref,
                    source_row_id=config.source_row_id,
                    expected_claim_id=config.input_claim_id,
                    expected_field="electricity_kwh",
                    witness_id=source_witness_id,
                ),
            ),
        ),
    )


def write_synthetic_run(run: SyntheticRun, run_dir: Path) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "master").mkdir(exist_ok=True)
    (run_dir / "raw_sources").mkdir(exist_ok=True)
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
        run.oracle.expected_obligations,
    )
    _write_csv(
        run_dir / "oracle" / "expected_hazards.csv",
        ["hazard_id", "kind", "field", "severity"],
        run.oracle.expected_hazards,
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


def _multiply(left: int | float, right: int | float) -> int | float:
    value = Decimal(str(left)) * Decimal(str(right))
    if value == value.to_integral_value():
        return float(value)
    return float(value)


__all__ = [
    "ExpectedClaim",
    "ExpectedDerivedClaim",
    "ExpectedSourceMap",
    "MasterReferenceRecord",
    "OUTPUT_CONTRACT",
    "RawElectricityRow",
    "SyntheticMaster",
    "SyntheticOracle",
    "SyntheticRawSources",
    "SyntheticRun",
    "generate_synthetic_pcf_run",
    "write_synthetic_run",
]
