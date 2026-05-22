from __future__ import annotations

from dataclasses import replace

import pytest

from comp.compiler_tool import resolve_reference_grounded_calculation
from comp.scenarios.synthetic import (
    SyntheticPcfAdapter,
    SyntheticScenarioConfig,
    generate_synthetic_pcf_run,
    write_synthetic_run,
)
from tests.support.synthetic.oracle_assertions import (
    assert_synthetic_oracle_matches_report,
    load_synthetic_oracle,
)


def test_oracle_assertions_match_smoke_report_outputs() -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_smoke(seed=7))
    adapter = SyntheticPcfAdapter(run.input_bundle)
    report = resolve_reference_grounded_calculation(
        adapter.blocked_report(),
        adapter.reference_catalog(),
        query_for_obligation=adapter.query_for_obligation,
        criteria=adapter.reference_selection_criteria(),
        input_claim=adapter.input_claim(),
        formula=adapter.formula(),
        output_claim_id=adapter.output_claim_id,
    )

    assert_synthetic_oracle_matches_report(run.oracle, report)


def test_oracle_assertions_match_anomaly_report_outputs() -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_anomaly(seed=11))
    adapter = SyntheticPcfAdapter(run.input_bundle)

    assert_synthetic_oracle_matches_report(run.oracle, adapter.anomaly_report())


def test_oracle_assertions_can_load_written_oracle_files(tmp_path) -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_anomaly(seed=11))
    run_dir = write_synthetic_run(run, tmp_path / "synthetic-pcf-anomaly")
    adapter = SyntheticPcfAdapter(run.input_bundle)

    oracle = load_synthetic_oracle(run_dir / "oracle")

    assert_synthetic_oracle_matches_report(oracle, adapter.anomaly_report())


def test_oracle_assertions_fail_when_expected_validation_requirement_is_missing() -> None:
    run = generate_synthetic_pcf_run(SyntheticScenarioConfig.pcf_anomaly(seed=11))
    adapter = SyntheticPcfAdapter(run.input_bundle)
    report = adapter.anomaly_report()
    report_without_site_alias = replace(report, validation_requirements=report.validation_requirements[:-1])

    with pytest.raises(AssertionError, match="expected validation requirements"):
        assert_synthetic_oracle_matches_report(
            run.oracle,
            report_without_site_alias,
        )
