from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from comp.compiler_tool import CompileReport
from comp.scenarios.synthetic import (
    ExpectedClaim,
    ExpectedDerivedClaim,
    ExpectedFailedClaim,
    ExpectedHazard,
    ExpectedObligation,
    ExpectedSourceMap,
    InjectedAnomaly,
    SyntheticOracle,
)


def load_synthetic_oracle(oracle_dir: Path) -> SyntheticOracle:
    return SyntheticOracle(
        expected_claims=tuple(
            ExpectedClaim(
                claim_id=row["claim_id"],
                field=row["field"],
                value=_parse_scalar(row["value"]),
                unit=row["unit"] or None,
                witness_id=row["witness_id"],
                source_row_id=row["source_row_id"],
            )
            for row in _read_csv(oracle_dir / "expected_claims.csv")
        ),
        expected_derived_claims=tuple(
            ExpectedDerivedClaim(
                claim_id=row["claim_id"],
                field=row["field"],
                value=_parse_scalar(row["value"]),
                unit=row["unit"],
                formula_id=row["formula_id"],
            )
            for row in _read_csv(oracle_dir / "expected_derived_claims.csv")
        ),
        expected_obligations=tuple(
            ExpectedObligation(
                obligation_id=row["obligation_id"],
                kind=row["kind"],
                field=row["field"],
                reason=row["reason"],
            )
            for row in _read_csv(oracle_dir / "expected_obligations.csv")
        ),
        expected_hazards=tuple(
            ExpectedHazard(
                hazard_id=row["hazard_id"],
                kind=row["kind"],
                field=row["field"],
                severity=row["severity"],
            )
            for row in _read_csv(oracle_dir / "expected_hazards.csv")
        ),
        expected_failed_claims=tuple(
            ExpectedFailedClaim(
                failed_claim_id=row["failed_claim_id"],
                field=row["field"],
                value=_parse_scalar(row["value"]),
                reason=row["reason"],
                source_row_id=row["source_row_id"],
            )
            for row in _read_csv(oracle_dir / "expected_failed_claims.csv")
        ),
        injected_anomalies=tuple(
            InjectedAnomaly(
                anomaly_id=row["anomaly_id"],
                anomaly_type=row["anomaly_type"],
                source_row_id=row["source_row_id"],
                field=row["field"],
                description=row["description"],
            )
            for row in _read_csv(oracle_dir / "injected_anomalies.csv")
        ),
        source_to_expected_claim_map=tuple(
            ExpectedSourceMap(
                source_ref=row["source_ref"],
                source_row_id=row["source_row_id"],
                expected_claim_id=row["expected_claim_id"],
                expected_field=row["expected_field"],
                witness_id=row["witness_id"],
            )
            for row in _read_csv(oracle_dir / "source_to_expected_claim_map.csv")
        ),
    )


def assert_synthetic_oracle_matches_report(
    oracle: SyntheticOracle,
    report: CompileReport,
) -> None:
    assert _checked_claim_rows(report) == _expected_claim_rows(
        oracle
    ), "expected checked claims did not match report.checked_claims"
    assert _derived_claim_rows(report) == _expected_derived_claim_rows(
        oracle
    ), "expected derived claims did not match report.derived_claims"
    assert _failed_claim_rows(report) == _expected_failed_claim_rows(
        oracle
    ), "expected failed claims did not match report.failed_claims"
    assert _obligation_rows(report) == _expected_obligation_rows(
        oracle
    ), "expected obligations did not match report.obligations"
    assert _hazard_rows(report) == _expected_hazard_rows(
        oracle
    ), "expected hazards did not match report.hazards"
    _assert_source_map_matches_witnesses(oracle, report)


def _expected_claim_rows(oracle: SyntheticOracle) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.field, claim.value, claim.witness_id)
        for claim in oracle.expected_claims
    )


def _checked_claim_rows(report: CompileReport) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.field, claim.value, claim.witness_id)
        for claim in report.checked_claims
    )


def _expected_derived_claim_rows(
    oracle: SyntheticOracle,
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.claim_id, claim.field, claim.value, claim.unit, claim.formula_id)
        for claim in oracle.expected_derived_claims
    )


def _derived_claim_rows(report: CompileReport) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.claim_id, claim.field, claim.value, claim.unit, claim.formula_id)
        for claim in report.derived_claims
    )


def _expected_failed_claim_rows(
    oracle: SyntheticOracle,
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.field, claim.value, claim.reason)
        for claim in oracle.expected_failed_claims
    )


def _failed_claim_rows(report: CompileReport) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (claim.field, claim.value, claim.reason)
        for claim in report.failed_claims
    )


def _expected_obligation_rows(
    oracle: SyntheticOracle,
) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            obligation.obligation_id,
            obligation.kind,
            obligation.field,
            obligation.reason,
        )
        for obligation in oracle.expected_obligations
    )


def _obligation_rows(report: CompileReport) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            obligation.obligation_id
            or _stable_id(
                "proof_obligation",
                obligation.kind,
                obligation.field,
                obligation.reason,
            ),
            obligation.kind,
            obligation.field,
            obligation.reason,
        )
        for obligation in report.obligations
    )


def _expected_hazard_rows(oracle: SyntheticOracle) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (hazard.hazard_id, hazard.kind, hazard.field, hazard.severity)
        for hazard in oracle.expected_hazards
    )


def _hazard_rows(report: CompileReport) -> tuple[tuple[Any, ...], ...]:
    return tuple(
        (
            _stable_id("hazard", hazard.kind, hazard.field, hazard.severity),
            hazard.kind,
            hazard.field,
            hazard.severity,
        )
        for hazard in report.hazards
    )


def _assert_source_map_matches_witnesses(
    oracle: SyntheticOracle,
    report: CompileReport,
) -> None:
    actual = {
        (witness.field, witness.witness_id, witness.source, witness.span)
        for witness in report.evidence_witnesses
    }
    expected = {
        (
            source_map.expected_field,
            source_map.witness_id,
            f"raw_sources/{source_map.source_ref}",
            source_map.source_row_id,
        )
        for source_map in oracle.source_to_expected_claim_map
    }
    missing = expected - actual
    assert not missing, (
        "source_to_expected_claim_map did not match report.evidence_witnesses: "
        f"{sorted(missing)}"
    )


def _stable_id(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


def _read_csv(path: Path) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        return tuple(csv.DictReader(handle))


def _parse_scalar(value: str) -> str | int | float:
    try:
        integer = int(value)
    except ValueError:
        pass
    else:
        return integer

    try:
        return float(value)
    except ValueError:
        return value


__all__ = ["assert_synthetic_oracle_matches_report", "load_synthetic_oracle"]
