from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from examples.product_facade_lab.bundle import verify_verification_bundle_file


CONFORMANCE_CASES_SCHEMA_VERSION = "product_facade_conformance_cases.v0"

FIXTURE_EXPECTED_REPLAY_STATUS = {
    "canonical_verification_bundle.json": "verified",
    "missing_artifact_verification_bundle.json": "blocked",
}


@dataclass(frozen=True)
class VerificationBundleFixtureResult:
    fixture_name: str
    path: Path
    expected_replay_status: str
    replay_status: str
    receipt_authenticity_status: str
    receipt_authenticity_errors: tuple[str, ...]
    public_row_id: str
    artifact_count: int
    verification_errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.replay_status == self.expected_replay_status


@dataclass(frozen=True)
class VerificationBundleCaseResult:
    case_id: str
    bundle_name: str
    path: Path
    expected_replay_status: str
    replay_status: str
    expected_receipt_authenticity_status: str
    receipt_authenticity_status: str
    expected_verification_error_contains: str | None
    public_row_id: str
    artifact_count: int
    verification_errors: tuple[str, ...]
    receipt_authenticity_errors: tuple[str, ...]

    @property
    def passed(self) -> bool:
        replay_matches = self.replay_status == self.expected_replay_status
        authenticity_matches = (
            self.receipt_authenticity_status
            == self.expected_receipt_authenticity_status
        )
        return replay_matches and authenticity_matches and self._expected_error_matches()

    def _expected_error_matches(self) -> bool:
        if self.expected_verification_error_contains is None:
            return True
        return any(
            self.expected_verification_error_contains in error
            for error in self.verification_errors
        )


def run_fixture(
    path: str | Path,
    *,
    key_registry=None,
) -> VerificationBundleFixtureResult:
    fixture_path = Path(path)
    expected_status = _expected_replay_status(fixture_path)
    output = verify_verification_bundle_file(fixture_path, key_registry=key_registry)
    return VerificationBundleFixtureResult(
        fixture_name=fixture_path.name,
        path=fixture_path,
        expected_replay_status=expected_status,
        replay_status=output.replay_status,
        receipt_authenticity_status=output.receipt_authenticity_status,
        receipt_authenticity_errors=output.receipt_authenticity_errors,
        public_row_id=output.public_row_id,
        artifact_count=output.artifact_count,
        verification_errors=output.verification_errors,
    )


def run_all_fixtures(
    fixture_dir: str | Path = Path(__file__).with_name("fixtures"),
    *,
    key_registry=None,
) -> tuple[VerificationBundleFixtureResult, ...]:
    root = Path(fixture_dir)
    return tuple(
        run_fixture(path, key_registry=key_registry)
        for path in sorted(root.glob("*_verification_bundle.json"))
    )


def run_case_manifest(
    path: str | Path,
    *,
    key_registry=None,
) -> tuple[VerificationBundleCaseResult, ...]:
    manifest_path = Path(path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != CONFORMANCE_CASES_SCHEMA_VERSION:
        raise ValueError(
            "Product facade conformance case manifest must use "
            f"{CONFORMANCE_CASES_SCHEMA_VERSION}."
        )
    return run_conformance_cases(
        manifest["cases"],
        fixture_dir=manifest_path.parent,
        key_registry=key_registry,
    )


def run_conformance_cases(
    cases: Iterable[Mapping[str, Any]],
    *,
    fixture_dir: str | Path = Path(__file__).with_name("fixtures"),
    key_registry=None,
) -> tuple[VerificationBundleCaseResult, ...]:
    root = Path(fixture_dir)
    return tuple(
        _run_conformance_case(case, fixture_dir=root, key_registry=key_registry)
        for case in cases
    )


def _expected_replay_status(path: Path) -> str:
    try:
        return FIXTURE_EXPECTED_REPLAY_STATUS[path.name]
    except KeyError as exc:
        raise ValueError(f"Unknown product facade bundle fixture: {path.name}") from exc


def _run_conformance_case(
    case: Mapping[str, Any],
    *,
    fixture_dir: Path,
    key_registry,
) -> VerificationBundleCaseResult:
    _reject_product_generated_replay_report(case)
    bundle_path = _bundle_path(case["bundle"], fixture_dir=fixture_dir)
    output = verify_verification_bundle_file(bundle_path, key_registry=key_registry)
    return VerificationBundleCaseResult(
        case_id=str(case["case_id"]),
        bundle_name=bundle_path.name,
        path=bundle_path,
        expected_replay_status=str(case["expected_replay_status"]),
        replay_status=output.replay_status,
        expected_receipt_authenticity_status=str(
            case["expected_receipt_authenticity_status"]
        ),
        receipt_authenticity_status=output.receipt_authenticity_status,
        expected_verification_error_contains=_optional_string(
            case.get("expected_verification_error_contains")
        ),
        public_row_id=output.public_row_id,
        artifact_count=output.artifact_count,
        verification_errors=output.verification_errors,
        receipt_authenticity_errors=output.receipt_authenticity_errors,
    )


def _bundle_path(bundle: object, *, fixture_dir: Path) -> Path:
    path = Path(str(bundle))
    if path.is_absolute():
        return path
    return fixture_dir / path


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _reject_product_generated_replay_report(case: Mapping[str, Any]) -> None:
    forbidden = {
        "expected_projection_replay_report",
        "projection_replay_report",
        "replay_report",
    }
    if forbidden.intersection(case):
        raise ValueError(
            "Product facade conformance cases must not include "
            "product-generated replay reports."
        )


__all__ = [
    "CONFORMANCE_CASES_SCHEMA_VERSION",
    "VerificationBundleCaseResult",
    "VerificationBundleFixtureResult",
    "run_all_fixtures",
    "run_case_manifest",
    "run_conformance_cases",
    "run_fixture",
]
