from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from comp.scenarios.synthetic.config import SyntheticScenarioConfig
from comp.scenarios.synthetic.models import (
    ExpectedDependencyRef,
    SYNTHETIC_SOURCE_INPUT_KIND,
    SyntheticLoadedSource,
    SyntheticMaster,
    SyntheticRawSources,
    SyntheticResolutionArtifacts,
)


def synthetic_source_input_dependency_id(
    config: SyntheticScenarioConfig,
    *,
    role: str,
    source_ref: str,
) -> str:
    return (
        f"{SYNTHETIC_SOURCE_INPUT_KIND}:{config.scenario_id}:"
        f"seed-{config.seed}:{role}:{source_ref}"
    )


def build_synthetic_loaded_source(
    *,
    source_ref: str,
    role: str,
    path: str,
    media_type: str,
    schema_id: str,
    rows: Iterable[dict[str, Any]],
) -> SyntheticLoadedSource:
    canonical_rows = tuple(dict(row) for row in rows)
    return SyntheticLoadedSource(
        source_ref=source_ref,
        role=role,
        path=path,
        media_type=media_type,
        schema_id=schema_id,
        row_count=len(canonical_rows),
        content_digest=_synthetic_source_content_digest(canonical_rows),
    )


def build_synthetic_loaded_sources(
    manifest: dict[str, Any],
    *,
    master: SyntheticMaster,
    raw_sources: SyntheticRawSources,
    resolution_artifacts: SyntheticResolutionArtifacts = SyntheticResolutionArtifacts(),
) -> tuple[SyntheticLoadedSource, ...]:
    return tuple(
        build_synthetic_loaded_source(
            source_ref=str(source["source_ref"]),
            role=str(source["role"]),
            path=str(source["path"]),
            media_type=str(source["media_type"]),
            schema_id=str(source["schema_id"]),
            rows=_source_rows_for_manifest_source(
                master,
                raw_sources,
                resolution_artifacts,
                role=str(source["role"]),
                source_ref=str(source["source_ref"]),
            ),
        )
        for source in manifest.get("sources", ())
        if isinstance(source, dict)
    )


def _source_rows_for_manifest_source(
    master: SyntheticMaster,
    raw_sources: SyntheticRawSources,
    resolution_artifacts: SyntheticResolutionArtifacts,
    *,
    role: str,
    source_ref: str,
) -> tuple[dict[str, Any], ...]:
    if role == "master_reference_catalog":
        return tuple(record.to_row() for record in master.reference_catalog)
    if role == "master_sites":
        return tuple(dict(row) for row in master.sites)
    if role == "master_products":
        return tuple(dict(row) for row in master.products)
    if role == "raw_source":
        return tuple(
            row.to_row()
            for row in raw_sources.electricity_rows
            if row.source_ref == source_ref
        )
    if role == "resolution_unit_witness":
        return tuple(
            artifact.to_row()
            for artifact in resolution_artifacts.unit_witnesses
            if artifact.source_ref == source_ref
        )
    return ()


def _synthetic_source_content_digest(rows: tuple[dict[str, Any], ...]) -> str:
    encoded = json.dumps(
        {"rows": rows},
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def synthetic_source_dependency_refs(
    config: SyntheticScenarioConfig,
) -> tuple[ExpectedDependencyRef, ...]:
    return tuple(
        ExpectedDependencyRef(
            dependency_kind=SYNTHETIC_SOURCE_INPUT_KIND,
            dependency_id=synthetic_source_input_dependency_id(
                config,
                role=role,
                source_ref=source_ref,
            ),
        )
        for role, source_ref in _synthetic_source_identities(config)
    )


def _synthetic_source_identities(
    config: SyntheticScenarioConfig,
) -> tuple[tuple[str, str], ...]:
    identities = (
        ("master_reference_catalog", "reference_catalog.csv"),
        ("master_sites", "sites.csv"),
        ("master_products", "products.csv"),
        ("raw_source", config.source_ref),
    )
    if config.scenario_id == "synthetic_pcf.resolution.v1":
        return (*identities, ("resolution_unit_witness", "unit_witnesses.csv"))
    return identities


__all__ = [
    "build_synthetic_loaded_source",
    "build_synthetic_loaded_sources",
    "synthetic_source_dependency_refs",
    "synthetic_source_input_dependency_id",
]
