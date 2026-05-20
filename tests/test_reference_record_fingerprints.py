from comp.compiler_tool import ReferenceRecord, reference_record_fingerprint


def _record(*, factor_value=0.42):
    return ReferenceRecord(
        reference_id="pcf.factor.kr_grid_2024.location_based",
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
