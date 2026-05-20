EXPECTED_PROJECTION = {
    "electricity_kwh": 1200,
    "reporting_year": 2024,
    "co2e_kg": 504.0,
}

EXPECTED_REFERENCE_CANDIDATE_IDS = (
    "pcf.factor.kr_grid_2024.location_based",
    "pcf.factor.kr_grid_2023.location_based",
)

EXPECTED_RESOLVED_OBLIGATION_KINDS = (
    "reference_search_required",
    "calculation_blocked",
)

