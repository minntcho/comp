from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from examples.product_facade_lab.bundle import verify_verification_bundle_file


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
        for path in sorted(root.glob("*.json"))
    )


def _expected_replay_status(path: Path) -> str:
    try:
        return FIXTURE_EXPECTED_REPLAY_STATUS[path.name]
    except KeyError as exc:
        raise ValueError(f"Unknown product facade bundle fixture: {path.name}") from exc


__all__ = [
    "VerificationBundleFixtureResult",
    "run_all_fixtures",
    "run_fixture",
]
