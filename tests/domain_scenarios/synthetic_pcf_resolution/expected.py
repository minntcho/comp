EXPECTED_PROJECTION = {
    "electricity_kwh": 1200,
    "co2e_kg": 504.0,
}

EXPECTED_REFERENCE_CANDIDATE_IDS = (
    "synthetic.factor.kr_grid_2024.location_based",
)

EXPECTED_RESOLVED_OBLIGATION_KINDS = (
    "find_source_witness",
    "reference_search_required",
    "calculation_blocked",
)

EXPECTED_RESOLVED_OBLIGATION_IDS = (
    "synthetic-obligation:missing_unit",
    "resolve:pcf.electricity_factor_multiplication.v1:"
    "synthetic-pcf-resolution:electricity:co2e_kg:reference_search_required",
    "calculation:pcf.electricity_factor_multiplication.v1:"
    "synthetic-pcf-resolution:electricity:co2e_kg:unknown_reference",
)

__all__ = [
    "EXPECTED_PROJECTION",
    "EXPECTED_REFERENCE_CANDIDATE_IDS",
    "EXPECTED_RESOLVED_OBLIGATION_IDS",
    "EXPECTED_RESOLVED_OBLIGATION_KINDS",
]
