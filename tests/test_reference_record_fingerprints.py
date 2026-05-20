from comp.compiler_tool import (
    ReferenceCatalog,
    ReferenceCatalogSnapshot,
    ReferenceRecord,
    reference_catalog_snapshot_fingerprint,
    reference_record_fingerprint,
)


def _record(
    *,
    reference_id="pcf.factor.kr_grid_2024.location_based",
    factor_value=0.42,
):
    return ReferenceRecord(
        reference_id=reference_id,
        reference_type="emission_factor",
        labels=("Korea grid electricity factor 2024",),
        aliases=("KR electricity grid factor",),
        description="Location-based electricity emission factor for Korea in 2024.",
        attributes=(
            ("geography", "KR"),
            ("valid_period", "2024"),
            ("factor_value", factor_value),
        ),
        source="pcf-reference-catalog-v1",
        witness_ids=("factor-row-kr-grid-2024",),
    )


def test_reference_record_fingerprint_pins_canonical_record_body():
    fingerprint = reference_record_fingerprint(_record())
    same_fingerprint = reference_record_fingerprint(_record())
    changed_fingerprint = reference_record_fingerprint(_record(factor_value=0.43))

    assert fingerprint.dependency_kind == "reference_record"
    assert fingerprint.dependency_id == "pcf.factor.kr_grid_2024.location_based"
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == same_fingerprint
    assert fingerprint != changed_fingerprint


def test_reference_catalog_snapshot_fingerprint_pins_record_manifest():
    catalog = ReferenceCatalog(
        records=(
            _record(),
            _record(
                reference_id="pcf.factor.kr_grid_2023.location_based",
                factor_value=0.43,
            ),
        )
    )
    snapshot = ReferenceCatalogSnapshot.from_catalog(
        catalog,
        catalog_id="pcf-reference-catalog",
        catalog_version="2026.1",
        selected_reference_ids=("pcf.factor.kr_grid_2024.location_based",),
    )
    same_snapshot = ReferenceCatalogSnapshot.from_catalog(
        catalog,
        catalog_id="pcf-reference-catalog",
        catalog_version="2026.1",
        selected_reference_ids=("pcf.factor.kr_grid_2024.location_based",),
    )
    changed_snapshot = ReferenceCatalogSnapshot.from_catalog(
        catalog,
        catalog_id="pcf-reference-catalog",
        catalog_version="2026.2",
        selected_reference_ids=("pcf.factor.kr_grid_2024.location_based",),
    )

    fingerprint = reference_catalog_snapshot_fingerprint(snapshot)

    assert snapshot.snapshot_id == "reference_catalog_snapshot:pcf-reference-catalog:2026.1"
    assert tuple(record.dependency_id for record in snapshot.record_fingerprints) == (
        "pcf.factor.kr_grid_2024.location_based",
    )
    assert fingerprint.dependency_kind == "reference_catalog_snapshot"
    assert fingerprint.dependency_id == snapshot.snapshot_id
    assert fingerprint.fingerprint.startswith("sha256:")
    assert fingerprint == reference_catalog_snapshot_fingerprint(same_snapshot)
    assert fingerprint != reference_catalog_snapshot_fingerprint(changed_snapshot)
