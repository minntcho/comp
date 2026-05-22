import pytest

from comp import PublicOutputSpec
from comp.compiler_tool import active_retrieval_query_policies
from comp.persistence import ArtifactEnvelope, ArtifactRef, ProjectionReplayBlocked
from tests.domain_scenarios.assertions import assert_projection_tamper_blocked
from tests.domain_scenarios.canonical_working_loop.fixtures import (
    RAW_EVIDENCE,
    compile_raw_evidence,
    extract_raw_evidence,
    open_calculation_obligation,
    profile,
)
from tests.domain_scenarios.canonical_working_loop.scenario import (
    SCENARIO,
    run_canonical_working_loop_scenario,
)
from tests.domain_scenarios.core import assert_scenario_contract, run_scenario
from tests.domain_scenarios.persistence import (
    replay_scenario_projection,
    scenario_replay_bundle,
)


def test_canonical_working_loop_extracts_and_compiles_raw_text():
    hypothesis = extract_raw_evidence(RAW_EVIDENCE)

    assert hypothesis.subject_id == "product:canonical-raw-pcf-1"
    assert [(claim.field, claim.value) for claim in hypothesis.claims] == [
        ("activity", "electricity"),
        ("electricity_kwh", 1200),
        ("unit", "kWh"),
        ("reporting_year", 2024),
        ("geography", "KR"),
    ]
    assert all(witness.grounded for witness in hypothesis.witnesses)

    report = compile_raw_evidence(RAW_EVIDENCE)

    assert report.status == "accepted"
    assert [claim.field for claim in report.checked_claims] == [
        "activity",
        "electricity_kwh",
        "unit",
        "reporting_year",
        "geography",
    ]
    assert [witness.witness_id for witness in report.evidence_witnesses] == [
        "w-activity",
        "w-electricity-kwh",
        "w-unit",
        "w-reporting-year",
        "w-geography",
    ]
    assert report.obligations == ()
    assert report.can_build_public_output is False


def test_canonical_working_loop_opens_calculation_obligation_after_compile():
    report = open_calculation_obligation(compile_raw_evidence(RAW_EVIDENCE))

    assert report.status == "blocked"
    assert [obligation.kind for obligation in report.obligations] == [
        "calculation_blocked",
    ]
    assert report.obligations[0].reason == "unknown_reference"
    assert report.derived_claims == ()


def test_canonical_working_loop_runs_raw_text_to_receipt_projection():
    result = run_scenario(SCENARIO)

    assert result.scenario_id == "canonical_working_loop.raw_text_pcf.v1"
    assert result.resolver_steps == (
        "raw_text_fixture",
        "deterministic_extractor_stub",
        "compiler_tool.compile_interpretation",
        "open_calculation_obligation",
        "plan_calculation_resolution",
        "resolver_tasks_from_report",
        "profile_active_retrieval_policy",
        "resolver_task_to_reference_query",
        "reference_retrieval:embedding_stub:factor",
        "deterministic_reference_selection",
        "retry_calculation",
        "prepare_commit",
        "receipt_gated_projection",
    )
    assert_scenario_contract(result, SCENARIO.contract)
    assert [
        candidate.retrieval_method for candidate in result.report.reference_candidates
    ] == [
        "embedding_stub:factor",
        "embedding_stub:factor",
    ]
    assert result.report.reference_bindings[0].selected_candidate_id == (
        "embedding_stub:factor:idx-canonical-kr-grid-2024"
    )
    assert result.projection == {
        "electricity_kwh": 1200,
        "reporting_year": 2024,
        "co2e_kg": 504.0,
    }


def test_canonical_working_loop_pins_retrieval_policy_in_profile():
    scenario_profile = profile()

    assert scenario_profile.active_retrieval_policy_ids == (
        "pcf-canonical-retrieval-query-policy-v1",
    )
    assert tuple(
        policy.policy_id
        for policy in active_retrieval_query_policies(scenario_profile)
    ) == ("pcf-canonical-retrieval-query-policy-v1",)


def test_canonical_working_loop_receipt_rejects_tampered_projection_value():
    result = run_canonical_working_loop_scenario()

    assert_projection_tamper_blocked(
        result,
        PublicOutputSpec(
            "canonical-pcf-public-row",
            ("electricity_kwh", "reporting_year", "co2e_kg"),
        ),
        {"co2e_kg": 999999},
        match="value commitment",
    )


def test_canonical_working_loop_replays_projection_from_stored_artifacts():
    result = run_canonical_working_loop_scenario()
    projection = PublicOutputSpec(
        "canonical-pcf-public-row",
        ("electricity_kwh", "reporting_year", "co2e_kg"),
    )

    replay = replay_scenario_projection(result, projection)

    assert replay.public_row == result.projection
    assert ArtifactRef(
        "commit-package:product:canonical-raw-pcf-1",
        "commit_package",
    ) in replay.artifact_refs
    assert ArtifactRef(
        "governance-decision:commit-package:product:canonical-raw-pcf-1",
        "governance_decision",
    ) in replay.artifact_refs
    assert ArtifactRef(
        "checked_claim:electricity_kwh:w-electricity-kwh",
        "checked_claim",
    ) in replay.artifact_refs
    assert ArtifactRef(
        "canonical-raw:co2e_kg",
        "derived_claim",
    ) in replay.artifact_refs
    assert ArtifactRef(
        "trace:canonical-raw:co2e_kg",
        "calculation_trace",
    ) in replay.artifact_refs
    assert dict(replay.artifact_digests)[
        "canonical-raw:co2e_kg"
    ].startswith("sha256:")
    assert tuple(
        (fingerprint.dependency_kind, fingerprint.dependency_id)
        for fingerprint in replay.dependency_fingerprints
    ) == (
        ("compiler_profile", "pcf-canonical-loop-v1"),
        ("domain_pack", "domain_pack:canonical-pcf:2026.1"),
        (
            "calculation_formula",
            "calculation_formula:pcf.electricity_factor_multiplication.v1",
        ),
        ("evidence_witness", "w-activity"),
        ("evidence_witness", "w-electricity-kwh"),
        ("evidence_witness", "w-unit"),
        ("evidence_witness", "w-reporting-year"),
        ("evidence_witness", "w-geography"),
        (
            "reference_catalog_snapshot",
            "reference_catalog_snapshot:pcf-reference-catalog:pcf-reference-catalog-v1",
        ),
        ("reference_record", "pcf.factor.kr_grid_2024.location_based"),
    )


def test_canonical_working_loop_replay_blocks_when_source_span_drifts():
    result = run_canonical_working_loop_scenario()
    projection = PublicOutputSpec(
        "canonical-pcf-public-row",
        ("electricity_kwh", "reporting_year", "co2e_kg"),
    )
    assert result.preparation.receipt is not None
    assert result.preparation.receipt.citations is not None
    fingerprint = next(
        fingerprint
        for fingerprint in result.preparation.receipt.citations.dependency_fingerprints
        if (
            fingerprint.dependency_kind == "evidence_witness"
            and fingerprint.dependency_id == "w-electricity-kwh"
        )
    )
    bundle = scenario_replay_bundle(
        result,
        override=ArtifactEnvelope.from_body(
            artifact_id="w-electricity-kwh",
            artifact_kind="evidence_witness",
            schema_version="domain-scenario-v1",
            body={
                "dependency_kind": "evidence_witness",
                "dependency_id": "w-electricity-kwh",
                "witness_id": "w-electricity-kwh",
                "field": "electricity_kwh",
                "source": "raw-evidence:canonical-working-loop",
                "span": "9999kWh",
                "text": RAW_EVIDENCE,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
            },
        ),
    )

    with pytest.raises(ProjectionReplayBlocked, match="source evidence"):
        replay_scenario_projection(result, projection, bundle=bundle)


def test_canonical_working_loop_replay_blocks_when_cited_artifact_is_missing():
    result = run_canonical_working_loop_scenario()
    projection = PublicOutputSpec(
        "canonical-pcf-public-row",
        ("electricity_kwh", "reporting_year", "co2e_kg"),
    )
    bundle = scenario_replay_bundle(
        result,
        skip=ArtifactRef("canonical-raw:co2e_kg", "derived_claim"),
    )

    with pytest.raises(ProjectionReplayBlocked, match="missing artifact"):
        replay_scenario_projection(result, projection, bundle=bundle)


def test_canonical_working_loop_records_readable_profile_lock_manifest():
    result = run_canonical_working_loop_scenario()
    bundle = scenario_replay_bundle(result)

    profile_envelope = bundle.artifacts.get("pcf-canonical-loop-v1")

    assert profile_envelope.artifact_kind == "compiler_profile"
    assert profile_envelope.body["dependency_kind"] == "compiler_profile"
    assert profile_envelope.body["dependency_id"] == "pcf-canonical-loop-v1"
    assert profile_envelope.body["fingerprint"].startswith("sha256:")
    assert profile_envelope.body["profile_lock"]["profile_id"] == (
        "pcf-canonical-loop-v1"
    )
    assert profile_envelope.body["profile_lock"]["active_retrieval_policy_ids"] == (
        "pcf-canonical-retrieval-query-policy-v1",
    )
