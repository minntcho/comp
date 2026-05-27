from __future__ import annotations

from pathlib import Path

import pytest

from examples.product_facade_lab.runner import (
    run_all_fixtures,
    run_case_manifest,
    run_conformance_cases,
    run_fixture,
)


FIXTURE_DIR = Path("examples/product_facade_lab/fixtures")


def test_canonical_verification_bundle_fixture_is_verified():
    result = run_fixture(FIXTURE_DIR / "canonical_verification_bundle.json")

    assert result.fixture_name == "canonical_verification_bundle.json"
    assert result.expected_replay_status == "verified"
    assert result.replay_status == "verified"
    assert result.receipt_authenticity_status == "unsigned_legacy"
    assert result.receipt_authenticity_errors == ()
    assert result.passed is True
    assert result.verification_errors == ()
    assert result.public_row_id == "public-row-fixture-canonical"
    assert result.artifact_count > 0


def test_missing_artifact_verification_bundle_fixture_is_blocked():
    result = run_fixture(FIXTURE_DIR / "missing_artifact_verification_bundle.json")

    assert result.fixture_name == "missing_artifact_verification_bundle.json"
    assert result.expected_replay_status == "blocked"
    assert result.replay_status == "blocked"
    assert result.receipt_authenticity_status == "unsigned_legacy"
    assert result.receipt_authenticity_errors == ()
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


def test_case_manifest_runs_named_fixture_expectations():
    results = run_case_manifest(FIXTURE_DIR / "conformance_cases.json")

    assert tuple(result.case_id for result in results) == (
        "canonical_fixture_verified",
        "missing_artifact_fixture_blocked",
    )
    assert tuple(result.bundle_name for result in results) == (
        "canonical_verification_bundle.json",
        "missing_artifact_verification_bundle.json",
    )
    assert tuple(result.replay_status for result in results) == (
        "verified",
        "blocked",
    )
    assert tuple(result.receipt_authenticity_status for result in results) == (
        "unsigned_legacy",
        "unsigned_legacy",
    )
    assert all(result.passed for result in results)
    assert "Projection replay missing artifact" in results[1].verification_errors[0]


def test_run_conformance_cases_accepts_in_memory_case_definitions():
    cases = (
        {
            "case_id": "canonical_inline",
            "bundle": "canonical_verification_bundle.json",
            "expected_replay_status": "verified",
            "expected_receipt_authenticity_status": "unsigned_legacy",
        },
    )

    results = run_conformance_cases(cases, fixture_dir=FIXTURE_DIR)

    assert len(results) == 1
    assert results[0].case_id == "canonical_inline"
    assert results[0].passed is True
    assert results[0].public_row_id == "public-row-fixture-canonical"


def test_unknown_bundle_fixture_requires_explicit_expectation():
    with pytest.raises(ValueError, match="Unknown product facade bundle fixture"):
        run_fixture(FIXTURE_DIR / "new_unclassified_fixture.json")


def test_case_manifest_rejects_product_generated_replay_reports(tmp_path):
    manifest = tmp_path / "cases.json"
    manifest.write_text(
        """{
  "schema_version": "product_facade_conformance_cases.v0",
  "cases": [
    {
      "case_id": "bad_case",
      "bundle": "canonical_verification_bundle.json",
      "expected_replay_status": "verified",
      "expected_receipt_authenticity_status": "unsigned_legacy",
      "expected_projection_replay_report": "product-owned"
    }
  ]
}
""",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="product-generated replay reports"):
        run_case_manifest(manifest)
