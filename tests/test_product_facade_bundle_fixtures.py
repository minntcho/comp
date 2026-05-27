from __future__ import annotations

from pathlib import Path

import pytest

from examples.product_facade_lab.runner import run_all_fixtures, run_fixture


FIXTURE_DIR = Path("examples/product_facade_lab/fixtures")


def test_canonical_verification_bundle_fixture_is_verified():
    result = run_fixture(FIXTURE_DIR / "canonical_verification_bundle.json")

    assert result.fixture_name == "canonical_verification_bundle.json"
    assert result.expected_replay_status == "verified"
    assert result.replay_status == "verified"
    assert result.passed is True
    assert result.verification_errors == ()
    assert result.public_row_id == "public-row-fixture-canonical"
    assert result.artifact_count > 0


def test_missing_artifact_verification_bundle_fixture_is_blocked():
    result = run_fixture(FIXTURE_DIR / "missing_artifact_verification_bundle.json")

    assert result.fixture_name == "missing_artifact_verification_bundle.json"
    assert result.expected_replay_status == "blocked"
    assert result.replay_status == "blocked"
    assert result.passed is True
    assert result.verification_errors
    assert "Projection replay missing artifact" in result.verification_errors[0]
    assert result.public_row_id == "public-row-fixture-missing-artifact"


def test_run_all_fixtures_reports_compact_conformance_results():
    results = run_all_fixtures(FIXTURE_DIR)

    assert tuple(result.fixture_name for result in results) == (
        "canonical_verification_bundle.json",
        "missing_artifact_verification_bundle.json",
    )
    assert tuple(result.replay_status for result in results) == (
        "verified",
        "blocked",
    )
    assert all(result.passed for result in results)


def test_unknown_bundle_fixture_requires_explicit_expectation():
    with pytest.raises(ValueError, match="Unknown product facade bundle fixture"):
        run_fixture(FIXTURE_DIR / "new_unclassified_fixture.json")
