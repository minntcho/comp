from __future__ import annotations

import tomllib
from pathlib import Path

from examples.product_facade_lab import (
    ProductFacadeRuntime,
    ProductInput,
    ProductPolicyPreflightInput,
    ProductWitness,
    compare_touch_logs,
)


def test_canonical_fast_path_submit_publish_audit_records_touch_log():
    runtime = ProductFacadeRuntime()

    run = runtime.submit(
        ProductInput(
            run_id="run-1",
            subject_id="facility-1",
            public_row_id="public-row-1",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            values={"amount": 1200, "unit": "kWh"},
            witnesses=(
                ProductWitness(
                    field="amount",
                    source="invoice.pdf",
                    span="p1: electricity amount",
                    text="1200",
                ),
                ProductWitness(
                    field="unit",
                    source="invoice.pdf",
                    span="p1: electricity unit",
                    text="kWh",
                ),
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )

    assert run.status == "publishable"
    assert run.required_actions == ()
    assert run.touch_log.flow == "canonical_fast_path"
    assert run.touch_log.operation == "submit"
    assert run.touch_log.sync_required == (
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert run.touch_log.sync_required_if_publishing == ("PublicOutputReceipt",)
    assert "ArtifactEnvelope" in run.touch_log.deferred
    assert "ProjectionReplayReport" in run.touch_log.deferred
    assert run.touch_log.not_used == (
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    )

    public = runtime.publish(run.run_id)

    assert public.public_row == {"amount": 1200, "unit": "kWh"}
    assert public.touch_log.operation == "publish"
    assert "PublicOutputReceipt" in public.touch_log.sync_required
    assert "ArtifactEnvelope" in public.touch_log.deferred
    assert "DecisionLedger" in public.touch_log.not_used

    audit = runtime.audit(public.public_row_id)

    assert audit.replay_report.public_row == public.public_row
    assert audit.touch_log.operation == "audit"
    assert audit.touch_log.sync_required == (
        "ArtifactEnvelope",
        "ProjectionReplayReport",
    )
    assert audit.touch_log.not_used == ("ProofGraph",)
    assert audit.artifact_count == len(audit.replay_report.artifact_refs)


def test_product_facade_lab_stays_outside_packaged_comp_surface():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = set(pyproject["tool"]["setuptools"]["packages"])
    source = Path("examples/product_facade_lab/runtime.py").read_text(
        encoding="utf-8"
    )
    runtime_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("comp/runtime").glob("*.py")
    )

    assert "examples" not in packages
    assert "examples.product_facade_lab" not in packages
    assert "class ProductFacadeRuntime" in source
    assert "ProductFacadeRuntime" not in runtime_sources
    assert "ProductPolicyPreflightInput" not in runtime_sources


def test_policy_preflight_path_records_policy_handoff_before_validation():
    runtime = ProductFacadeRuntime()

    run = runtime.submit_policy_preflight(
        ProductPolicyPreflightInput(
            run_id="run-policy-1",
            subject_id="facility-1",
            public_row_id="public-row-policy-1",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            material_id="material:invoice-1",
            source_ref="invoice.pdf",
            values={"amount": 1200, "unit": "kWh"},
            witnesses=(
                ProductWitness(
                    field="amount",
                    source="invoice.pdf",
                    span="p1: electricity amount",
                    text="1200",
                ),
                ProductWitness(
                    field="unit",
                    source="invoice.pdf",
                    span="p1: electricity unit",
                    text="kWh",
                ),
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )

    assert run.status == "publishable"
    assert run.required_actions == ()
    assert run.touch_log.flow == "policy_preflight_path"
    assert run.touch_log.operation == "submit"
    assert run.touch_log.sync_required == (
        "MaterialDescriptor",
        "PolicyEffect",
        "PolicyAssembly",
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert run.touch_log.sync_required_if_publishing == ("PublicOutputReceipt",)
    assert "ArtifactEnvelope" in run.touch_log.deferred
    assert "ProjectionReplayReport" in run.touch_log.deferred
    assert "ProductPolicyPreflightInput" in run.touch_log.product_only
    assert any("DecisionLedger" in note for note in run.touch_log.notes)

    public = runtime.publish(run.run_id)

    assert public.public_row == {"amount": 1200, "unit": "kWh"}
    assert public.touch_log.flow == "policy_preflight_path"
    assert "PublicOutputReceipt" in public.touch_log.sync_required
    assert public.touch_log.not_used == ()
    assert any("receipt-gated projection" in note for note in public.touch_log.notes)

    audit = runtime.audit(public.public_row_id)

    assert audit.replay_report.public_row == public.public_row
    assert audit.touch_log.flow == "policy_preflight_path"
    assert audit.artifact_count == len(audit.replay_report.artifact_refs)


def test_submit_touch_log_comparison_summarizes_observed_ceremony_delta():
    runtime = ProductFacadeRuntime()
    canonical_run = runtime.submit(
        ProductInput(
            run_id="run-compare-canonical",
            subject_id="facility-1",
            public_row_id="public-row-compare-canonical",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            values={"amount": 1200, "unit": "kWh"},
            witnesses=(
                ProductWitness(
                    field="amount",
                    source="invoice.pdf",
                    span="p1: electricity amount",
                    text="1200",
                ),
                ProductWitness(
                    field="unit",
                    source="invoice.pdf",
                    span="p1: electricity unit",
                    text="kWh",
                ),
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )
    policy_run = runtime.submit_policy_preflight(
        ProductPolicyPreflightInput(
            run_id="run-compare-policy",
            subject_id="facility-1",
            public_row_id="public-row-compare-policy",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            material_id="material:invoice-compare",
            source_ref="invoice.pdf",
            values={"amount": 1200, "unit": "kWh"},
            witnesses=(
                ProductWitness(
                    field="amount",
                    source="invoice.pdf",
                    span="p1: electricity amount",
                    text="1200",
                ),
                ProductWitness(
                    field="unit",
                    source="invoice.pdf",
                    span="p1: electricity unit",
                    text="kWh",
                ),
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )

    comparison = compare_touch_logs(
        canonical_run.touch_log,
        policy_run.touch_log,
    )

    assert comparison.baseline_flow == "canonical_fast_path"
    assert comparison.candidate_flow == "policy_preflight_path"
    assert comparison.operation == "submit"
    assert comparison.shared_sync_required == (
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert comparison.candidate_sync_only == (
        "MaterialDescriptor",
        "PolicyEffect",
        "PolicyAssembly",
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    )
    assert comparison.baseline_omitted_but_candidate_sync == (
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    )
    assert comparison.deferred_in_both == (
        "ArtifactEnvelope",
        "ProjectionReplayReport",
    )
    assert comparison.to_dict()["candidate_sync_only"] == [
        "MaterialDescriptor",
        "PolicyEffect",
        "PolicyAssembly",
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    ]
    assert any("observation summary" in note for note in comparison.notes)


def test_observation_map_points_to_canonical_lab_without_promoting_runtime():
    product_map = Path(
        "docs/architecture/maps/product-facade-observation.md"
    ).read_text(encoding="utf-8")
    lab_readme = Path("examples/product_facade_lab/README.md").read_text(
        encoding="utf-8"
    )

    assert "examples/product_facade_lab" in product_map
    assert "comp-backed observation lab" in lab_readme
    assert "not a production runtime" in lab_readme
    assert "policy preflight path" in lab_readme
    assert "compare_touch_logs" in lab_readme
    assert "observation summary" in product_map
    assert "native production authority engine" in lab_readme
