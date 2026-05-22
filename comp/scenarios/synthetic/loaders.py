from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    MasterReferenceRecord,
    RawElectricityRow,
    SyntheticLoadedSource,
    SyntheticInputBundle,
    SyntheticMaster,
    SyntheticRawSources,
    SyntheticResolutionArtifact,
    SyntheticResolutionArtifacts,
)
from comp.scenarios.synthetic.sources import (
    build_synthetic_loaded_source,
)


class SyntheticInputLoadError(ValueError):
    """Raised when a synthetic input directory cannot be loaded from manifest."""


@dataclass(frozen=True)
class SyntheticSourceDescriptor:
    source_ref: str
    role: str
    path: str
    media_type: str
    schema_id: str

    @classmethod
    def from_manifest(cls, payload: dict[str, Any]) -> "SyntheticSourceDescriptor":
        try:
            return cls(
                source_ref=str(payload["source_ref"]),
                role=str(payload["role"]),
                path=str(payload["path"]),
                media_type=str(payload["media_type"]),
                schema_id=str(payload["schema_id"]),
            )
        except KeyError as exc:
            raise SyntheticInputLoadError(
                f"synthetic source descriptor missing field: {exc.args[0]}"
            ) from exc


Loader = Callable[[Path, SyntheticSourceDescriptor], tuple[object, ...]]


def load_synthetic_input_bundle(run_dir: Path) -> SyntheticInputBundle:
    manifest = _read_manifest(run_dir)
    config = _config_from_manifest(manifest)
    descriptors = _source_descriptors(manifest)
    loaded, loaded_sources = _load_sources(run_dir, descriptors)

    return SyntheticInputBundle(
        config=config,
        manifest=manifest,
        master=SyntheticMaster(
            reference_catalog=tuple(
                loaded.get("master_reference_catalog", ())
            ),
            sites=tuple(loaded.get("master_sites", ())),
            products=tuple(loaded.get("master_products", ())),
        ),
        raw_sources=SyntheticRawSources(
            electricity_rows=tuple(loaded.get("raw_source", ())),
        ),
        resolution_artifacts=SyntheticResolutionArtifacts(
            unit_witnesses=tuple(loaded.get("resolution_unit_witness", ())),
        ),
        output_contract=tuple(manifest.get("output_contract", ())),
        loaded_sources=loaded_sources,
    )


def _read_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "manifest.json"
    if not path.is_file():
        raise SyntheticInputLoadError(f"missing synthetic manifest: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SyntheticInputLoadError("synthetic manifest must be a JSON object")
    return payload


def _config_from_manifest(manifest: dict[str, Any]) -> SyntheticScenarioConfig:
    payload = manifest.get("config")
    if not isinstance(payload, dict):
        raise SyntheticInputLoadError("synthetic manifest missing config object")
    return SyntheticScenarioConfig(
        **{
            **payload,
            "anomalies": tuple(payload.get("anomalies", ())),
        }
    )


def _source_descriptors(
    manifest: dict[str, Any],
) -> tuple[SyntheticSourceDescriptor, ...]:
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise SyntheticInputLoadError("synthetic manifest missing sources list")
    return tuple(
        SyntheticSourceDescriptor.from_manifest(source)
        for source in sources
        if isinstance(source, dict)
    )


def _load_sources(
    run_dir: Path,
    descriptors: tuple[SyntheticSourceDescriptor, ...],
) -> tuple[dict[str, tuple[object, ...]], tuple[SyntheticLoadedSource, ...]]:
    loaded: dict[str, tuple[object, ...]] = {}
    loaded_sources: list[SyntheticLoadedSource] = []
    for descriptor in descriptors:
        loader = _LOADER_REGISTRY.get((descriptor.media_type, descriptor.schema_id))
        if loader is None:
            raise SyntheticInputLoadError(
                "unsupported synthetic source loader: "
                f"{descriptor.media_type} {descriptor.schema_id}"
            )
        loaded_items = tuple(loader(run_dir / descriptor.path, descriptor))
        loaded[descriptor.role] = loaded.get(descriptor.role, ()) + loaded_items
        loaded_sources.append(
            build_synthetic_loaded_source(
                source_ref=descriptor.source_ref,
                role=descriptor.role,
                path=descriptor.path,
                media_type=descriptor.media_type,
                schema_id=descriptor.schema_id,
                rows=_rows_for_loaded_items(loaded_items),
            )
        )
    return loaded, tuple(loaded_sources)


def _load_reference_catalog_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[MasterReferenceRecord, ...]:
    return tuple(
        MasterReferenceRecord(
            reference_id=row["reference_id"],
            reference_type=row["reference_type"],
            label=row["label"],
            geography=row["geography"],
            valid_period=row["valid_period"],
            method=row["method"],
            factor_value=_number(row["factor_value"]),
            input_unit=row["input_unit"],
            output_unit=row["output_unit"],
            source=row["source"],
            witness_id=row["witness_id"],
        )
        for row in _read_csv(path, descriptor)
    )


def _load_sites_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[dict[str, Any], ...]:
    return tuple(dict(row) for row in _read_csv(path, descriptor))


def _load_products_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[dict[str, Any], ...]:
    return tuple(dict(row) for row in _read_csv(path, descriptor))


def _load_electricity_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[RawElectricityRow, ...]:
    return tuple(
        RawElectricityRow(
            source_row_id=row["source_row_id"],
            source_ref=row["source_ref"],
            period=row["period"],
            site_id=row["site_id"],
            site_name=row["site_name"],
            product_id=row["product_id"],
            activity_type=row["activity_type"],
            amount=_number(row["amount"]),
            unit=row["unit"],
        )
        for row in _read_csv(path, descriptor)
    )


def _load_resolution_unit_witnesses_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[SyntheticResolutionArtifact, ...]:
    return tuple(
        SyntheticResolutionArtifact(
            artifact_id=row["artifact_id"],
            obligation_id=row["obligation_id"],
            source_row_id=row["source_row_id"],
            field=row["field"],
            resolved_value=row["resolved_value"],
            witness_id=row["witness_id"],
            source_ref=row["source_ref"],
            rationale=row["rationale"],
        )
        for row in _read_csv(path, descriptor)
    )


def _read_csv(
    path: Path,
    descriptor: SyntheticSourceDescriptor,
) -> tuple[dict[str, str], ...]:
    if not path.is_file():
        raise SyntheticInputLoadError(
            f"missing synthetic source file for {descriptor.source_ref}: {path}"
        )
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(csv.DictReader(handle))


def _rows_for_loaded_items(
    loaded_items: tuple[object, ...],
) -> tuple[dict[str, Any], ...]:
    rows: list[dict[str, Any]] = []
    for item in loaded_items:
        if isinstance(
            item,
            (
                MasterReferenceRecord,
                RawElectricityRow,
                SyntheticResolutionArtifact,
            ),
        ):
            rows.append(item.to_row())
            continue
        if isinstance(item, dict):
            rows.append(dict(item))
            continue
        raise SyntheticInputLoadError(
            "synthetic source loader returned unsupported item: "
            f"{type(item).__name__}"
        )
    return tuple(rows)


def _number(value: str) -> int | float:
    number = Decimal(value)
    if number == number.to_integral_value():
        return int(number)
    return float(number)


_LOADER_REGISTRY: dict[tuple[str, str], Loader] = {
    ("text/csv", "synthetic.master_reference_catalog.v1"): _load_reference_catalog_csv,
    ("text/csv", "synthetic.master_sites.v1"): _load_sites_csv,
    ("text/csv", "synthetic.master_products.v1"): _load_products_csv,
    ("text/csv", "synthetic.erp_electricity.v1"): _load_electricity_csv,
    (
        "text/csv",
        "synthetic.resolution_unit_witnesses.v1",
    ): _load_resolution_unit_witnesses_csv,
}


__all__ = [
    "SyntheticInputLoadError",
    "SyntheticSourceDescriptor",
    "load_synthetic_input_bundle",
]
