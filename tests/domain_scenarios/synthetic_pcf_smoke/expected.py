EXPECTED_PROJECTION = {
    "electricity_kwh": 1200,
    "co2e_kg": 504.0,
}

EXPECTED_REFERENCE_CANDIDATE_IDS = (
    "synthetic.factor.kr_grid_2024.location_based",
)

EXPECTED_RESOLVED_OBLIGATION_KINDS = (
    "reference_search_required",
    "calculation_blocked",
)

__all__ = [
    "EXPECTED_PROJECTION",
    "EXPECTED_REFERENCE_CANDIDATE_IDS",
    "EXPECTED_RESOLVED_OBLIGATION_KINDS",
]
