import pytest

from comp.compiler_tool import (
    ReferenceCatalog,
    ReferenceLookupError,
    ReferenceRecord,
)


def _tiny_catalog():
    return ReferenceCatalog(
        records=(
            ReferenceRecord(
                reference_id="concept.electricity_consumption",
                reference_type="taxonomy_concept",
                labels=("Electricity consumption",),
                aliases=("purchased electricity", "scope 2 electricity"),
                description="Purchased electricity consumption activity.",
                attributes=(("claim_type", "activity_observation"),),
                source="tiny-fixture",
                witness_ids=("ref-concept-electricity",),
            ),
            ReferenceRecord(
                reference_id="unit.kwh",
                reference_type="unit",
                labels=("kWh",),
                aliases=("kilowatt hour", "kilowatt-hour"),
                attributes=(("dimension", "energy"),),
                source="tiny-fixture",
                witness_ids=("ref-unit-kwh",),
            ),
            ReferenceRecord(
                reference_id="factor.kr_grid.2024.location_based",
                reference_type="emission_factor",
                labels=("KR grid electricity factor 2024",),
                aliases=("korea electricity grid factor",),
                attributes=(
                    ("concept_id", "concept.electricity_consumption"),
                    ("geography", "KR"),
                    ("valid_period", "2024"),
                    ("method", "location_based"),
                    ("unit_basis", "kgCO2e/kWh"),
                ),
                source="tiny-fixture",
                witness_ids=("ref-factor-row-17",),
            ),
        )
    )


def test_reference_catalog_retrieves_canonical_record_by_id():
    catalog = _tiny_catalog()

    factor = catalog.get("factor.kr_grid.2024.location_based")

    assert factor.reference_type == "emission_factor"
    assert factor.attribute("geography") == "KR"
    assert factor.attribute("valid_period") == "2024"
    assert factor.attribute("method") == "location_based"


def test_reference_catalog_alias_search_returns_candidate_only_artifacts():
    catalog = _tiny_catalog()

    candidates = catalog.search(
        "purchased electricity",
        reference_type="taxonomy_concept",
    )

    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.reference_id == "concept.electricity_consumption"
    assert candidate.reference_type == "taxonomy_concept"
    assert candidate.retrieval_method == "keyword"
    assert candidate.retrieval_score == 1.0
    assert candidate.source == "tiny-fixture"
    assert candidate.witness_ids == ("ref-concept-electricity",)
    assert candidate.authority == "candidate_only"
    assert candidate.can_authorize_calculation is False


def test_reference_catalog_filters_by_reference_type():
    catalog = _tiny_catalog()

    candidates = catalog.search("electricity", reference_type="unit")

    assert candidates == ()


def test_reference_record_can_be_rendered_as_exact_candidate():
    catalog = _tiny_catalog()
    factor = catalog.get("factor.kr_grid.2024.location_based")

    candidate = factor.to_candidate(
        candidate_id="cand-factor-kr-grid-2024",
        retrieval_method="fixture_exact",
        retrieval_score=1.0,
    )

    assert candidate.reference_id == factor.reference_id
    assert candidate.reference_type == "emission_factor"
    assert candidate.source == "tiny-fixture"
    assert candidate.witness_ids == ("ref-factor-row-17",)
    assert candidate.authority == "candidate_only"


def test_reference_catalog_rejects_duplicate_ids_and_missing_lookup():
    with pytest.raises(ValueError, match="duplicate reference id"):
        ReferenceCatalog(
            records=(
                ReferenceRecord(
                    reference_id="unit.kwh",
                    reference_type="unit",
                ),
                ReferenceRecord(
                    reference_id="unit.kwh",
                    reference_type="unit",
                ),
            )
        )

    with pytest.raises(ReferenceLookupError, match="unknown reference id"):
        _tiny_catalog().get("missing.reference")
