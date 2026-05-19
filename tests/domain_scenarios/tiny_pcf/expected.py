EXPECTED_RESOLVED_OBLIGATION_KINDS = (
    "reference_search_required",
    "calculation_blocked",
)

EXPECTED_REFERENCE_CANDIDATE_IDS = (
    "pcf.factor.kr_grid_2024.location_based",
    "pcf.factor.kr_grid_2023.location_based",
)

EXPECTED_REJECTED_CANDIDATES = (
    (
        "pcf.factor.kr_grid_2023.location_based",
        "attribute_mismatch:valid_period",
    ),
)

EXPECTED_PROJECTION = {
    "electricity_kwh": 1200,
    "co2e_kg": 504.0,
}


__all__ = [
    "EXPECTED_PROJECTION",
    "EXPECTED_REFERENCE_CANDIDATE_IDS",
    "EXPECTED_REJECTED_CANDIDATES",
    "EXPECTED_RESOLVED_OBLIGATION_KINDS",
]
