EXPECTED_OPEN_OBLIGATION_IDS = (
    "synthetic-obligation:missing_unit",
    "synthetic-obligation:wrong_unit",
    "synthetic-obligation:period_mismatch",
    "synthetic-obligation:negative_amount",
    "synthetic-obligation:site_alias",
)

EXPECTED_HAZARD_IDS = (
    "hazard:missing_unit:unit:review",
    "hazard:period_mismatch:period:review",
    "hazard:invalid_activity_amount:electricity_kwh:block",
    "hazard:site_alias:site_id:review",
)

EXPECTED_FAILED_CLAIMS = (
    ("unit", "unsupported_unit"),
    ("electricity_kwh", "negative_amount"),
)

__all__ = [
    "EXPECTED_FAILED_CLAIMS",
    "EXPECTED_HAZARD_IDS",
    "EXPECTED_OPEN_OBLIGATION_IDS",
]
