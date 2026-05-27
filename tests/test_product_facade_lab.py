from __future__ import annotations

from dataclasses import replace
import json
import tomllib
from pathlib import Path

from examples.product_facade_lab import (
    CompCompatibleVerificationInput,
    CompVerificationOutput,
    ProductFacadeRuntime,
    ProductInput,
    ProductPolicyPreflightInput,
    ProductRequiredAction,
    ProductWitness,
    compare_touch_logs,
    verify_comp_compatible_input,
    verification_input_from_bundle,
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
    assert run.publishable is True
    assert run.user_message == "검증이 완료되어 공개할 수 있습니다."
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
    assert public.receipt_handle.startswith("receipt:commit-package:")
    assert public.replayable_now is False
    assert public.audit_pending is True
    assert public.touch_log.operation == "publish"
    assert "PublicOutputReceipt" in public.touch_log.sync_required
    assert "ArtifactEnvelope" in public.touch_log.deferred
    assert "DecisionLedger" in public.touch_log.not_used

    audit = runtime.audit(public.public_row_id)

    assert audit.replay_report.public_row == public.public_row
    assert audit.replay_status == "verified"
    assert audit.verification_errors == ()
    assert audit.proof_graph_available is False
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
    assert run.publishable is True
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
    assert public.receipt_handle.startswith("receipt:commit-package:")
    assert public.replayable_now is False
    assert public.audit_pending is True
    assert public.touch_log.flow == "policy_preflight_path"
    assert "PublicOutputReceipt" in public.touch_log.sync_required
    assert public.touch_log.not_used == ()
    assert any("receipt-gated projection" in note for note in public.touch_log.notes)

    audit = runtime.audit(public.public_row_id)

    assert audit.replay_report.public_row == public.public_row
    assert audit.replay_status == "verified"
    assert audit.verification_errors == ()
    assert audit.proof_graph_available is False
    assert audit.touch_log.flow == "policy_preflight_path"
    assert audit.artifact_count == len(audit.replay_report.artifact_refs)


def test_needs_evidence_submit_returns_product_facing_required_actions():
    runtime = ProductFacadeRuntime()

    run = runtime.submit(
        ProductInput(
            run_id="run-needs-evidence",
            subject_id="facility-1",
            public_row_id="public-row-needs-evidence",
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
            ),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )

    assert run.status == "needs_evidence"
    assert run.publishable is False
    assert run.user_message == "추가 증빙이 필요합니다."
    assert run.required_actions == (
        ProductRequiredAction(
            kind="find_source_witness",
            field="unit",
            reason="missing_source_witness",
            message_key="missing_evidence",
            message="근거자료가 연결되지 않아 이 값을 검증할 수 없습니다.",
            action="값이 나온 문서, 엑셀, 인증서 등의 위치를 연결해 주세요.",
        ),
    )
    assert "missing_source_witness" not in run.required_actions[0].message
    assert "missing_source_witness" not in run.required_actions[0].action
    assert run.touch_log.operation == "submit"
    assert "DecisionLedger" in run.touch_log.not_used


def test_comp_compatible_verification_input_exports_material_without_replay_report():
    runtime = ProductFacadeRuntime()
    public = _publish_canonical_runtime(runtime, "run-verification-input")

    verification_input = runtime.export_verification_input(public.public_row_id)

    assert isinstance(verification_input, CompCompatibleVerificationInput)
    assert verification_input.public_row_id == public.public_row_id
    assert verification_input.public_row == public.public_row
    assert verification_input.receipt_handle == public.receipt_handle
    assert verification_input.public_output_receipt.public_row_id == public.public_row_id
    assert verification_input.validation_summary == {
        "status": "accepted",
        "checked_claim_fields": ("amount", "unit"),
        "calculated_claim_fields": (),
        "validation_requirement_count": 0,
    }
    assert "publishable" not in verification_input.validation_summary
    assert "can_build_public_output" not in verification_input.validation_summary
    assert verification_input.artifact_envelopes
    assert verification_input.explanation_hints == ()
    assert verification_input.omitted_verification_outputs == (
        "ProjectionReplayReport",
        "ProofGraph",
    )
    assert "ProductInput" in verification_input.product_only_excluded
    assert "ProductRun" in verification_input.product_only_excluded
    assert "ProductPublicRow" in verification_input.product_only_excluded
    assert "touch_log" in verification_input.product_only_excluded
    assert not hasattr(verification_input, "replay_report")
    assert not hasattr(verification_input, "proof_graph")


def test_comp_verifier_produces_replay_report_from_verification_input():
    runtime = ProductFacadeRuntime()
    public = _publish_canonical_runtime(runtime, "run-verification-output")
    verification_input = runtime.export_verification_input(public.public_row_id)

    verification_output = verify_comp_compatible_input(verification_input)

    assert isinstance(verification_output, CompVerificationOutput)
    assert verification_output.public_row_id == public.public_row_id
    assert verification_output.replay_status == "verified"
    assert verification_output.verification_errors == ()
    assert verification_output.proof_graph_available is False
    assert verification_output.artifact_count == len(
        verification_input.artifact_envelopes
    )
    assert verification_output.replay_report is not None
    assert verification_output.replay_report.public_row == public.public_row


def test_comp_verifier_reports_blocked_input_without_trusting_product_claim():
    runtime = ProductFacadeRuntime()
    public = _publish_canonical_runtime(runtime, "run-verification-blocked")
    verification_input = runtime.export_verification_input(public.public_row_id)
    broken_input = replace(
        verification_input,
        artifact_envelopes=verification_input.artifact_envelopes[:-1],
    )

    verification_output = verify_comp_compatible_input(broken_input)

    assert verification_output.public_row_id == public.public_row_id
    assert verification_output.replay_status == "blocked"
    assert verification_output.replay_report is None
    assert verification_output.proof_graph_available is False
    assert verification_output.artifact_count == len(broken_input.artifact_envelopes)
    assert verification_output.verification_errors
    assert (
        "Projection replay missing artifact"
        in verification_output.verification_errors[0]
    )


def test_comp_compatible_verification_bundle_round_trips_through_json():
    runtime = ProductFacadeRuntime()
    public = _publish_canonical_runtime(runtime, "run-verification-bundle")

    bundle = runtime.export_verification_bundle(public.public_row_id)
    loaded_bundle = json.loads(json.dumps(bundle, sort_keys=True))
    verification_input = verification_input_from_bundle(loaded_bundle)
    verification_output = verify_comp_compatible_input(verification_input)

    assert bundle["schema_version"] == "product_facade_verification_bundle.v0"
    assert bundle["bundle_kind"] == "comp_compatible_verification_input"
    assert bundle["public_row_id"] == public.public_row_id
    assert bundle["public_row"] == public.public_row
    assert bundle["projection"] == {
        "projection_id": "public-row",
        "output_fields": ["amount", "unit"],
    }
    assert bundle["receipt_handle"] == public.receipt_handle
    assert bundle["validation_summary"]["status"] == "accepted"
    assert bundle["artifact_envelopes"]
    assert "ProjectionReplayReport" in bundle["omitted_verification_outputs"]
    assert "ProofGraph" in bundle["omitted_verification_outputs"]
    assert bundle["product_only_excluded"]
    assert "touch_log" in bundle["product_only_excluded"]
    assert "replay_report" not in bundle
    assert "projection_replay_report" not in bundle
    assert "proof_graph" not in bundle
    assert verification_output.replay_status == "verified"
    assert verification_output.replay_report is not None
    assert verification_output.replay_report.public_row == public.public_row


def test_write_verification_bundle_creates_json_file(tmp_path):
    runtime = ProductFacadeRuntime()
    public = _publish_canonical_runtime(runtime, "run-verification-file")
    bundle_path = tmp_path / "verification-bundle.json"

    written_path = runtime.write_verification_bundle(
        public.public_row_id,
        bundle_path,
    )
    loaded_bundle = json.loads(written_path.read_text(encoding="utf-8"))
    verification_output = verify_comp_compatible_input(
        verification_input_from_bundle(loaded_bundle)
    )

    assert written_path == bundle_path
    assert loaded_bundle["schema_version"] == "product_facade_verification_bundle.v0"
    assert loaded_bundle["public_row_id"] == public.public_row_id
    assert loaded_bundle["receipt_handle"] == public.receipt_handle
    assert "replay_report" not in loaded_bundle
    assert verification_output.replay_status == "verified"


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


def test_product_facade_lab_conforms_to_artifact_lifecycle_boundary():
    boundary_doc = _artifact_lifecycle_boundary()
    observations = _run_lifecycle_lab_observations()

    canonical_submit = observations["canonical_submit"]
    policy_submit = observations["policy_submit"]
    canonical_publish = observations["canonical_publish"]
    policy_publish = observations["policy_publish"]
    canonical_audit = observations["canonical_audit"]
    policy_audit = observations["policy_audit"]

    _assert_contract_mentions(
        boundary_doc,
        "canonical submit -> validation",
        canonical_submit.sync_required,
    )
    assert canonical_submit.sync_required == (
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert canonical_submit.not_used == (
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
    )
    assert "PublicOutputReceipt" in canonical_submit.sync_required_if_publishing

    _assert_contract_mentions(
        boundary_doc,
        "policy preflight submit -> validation",
        policy_submit.sync_required,
    )
    assert policy_submit.sync_required == (
        "MaterialDescriptor",
        "PolicyEffect",
        "PolicyAssembly",
        "DecisionLedger",
        "SelectedValidationContract",
        "ValidationHandoff",
        "InterpretationHypothesis",
        "ValidationReport",
    )
    assert "PublicOutputReceipt" not in policy_submit.sync_required

    expected_publish_sync = (
        "ValidationReport",
        "ReviewPackage",
        "ReviewDecision",
        "PublicOutputReceipt",
        "PublicOutputSpec",
    )
    _assert_contract_mentions(
        boundary_doc,
        "validated -> published",
        expected_publish_sync,
    )
    assert canonical_publish.sync_required == expected_publish_sync
    assert policy_publish.sync_required == expected_publish_sync
    assert "ArtifactEnvelope" not in canonical_publish.sync_required
    assert "ArtifactEnvelope" in canonical_publish.deferred
    assert "ArtifactEnvelope" not in policy_publish.sync_required
    assert "ArtifactEnvelope" in policy_publish.deferred
    assert "DecisionLedger" in canonical_publish.not_used
    assert any("receipt-gated projection" in note for note in policy_publish.notes)

    expected_audit_sync = ("ArtifactEnvelope", "ProjectionReplayReport")
    _assert_contract_mentions(
        boundary_doc,
        "published -> replayable/auditable",
        expected_audit_sync,
    )
    assert canonical_audit.sync_required == expected_audit_sync
    assert policy_audit.sync_required == expected_audit_sync
    assert canonical_audit.not_used == ("ProofGraph",)
    assert policy_audit.not_used == ("ProofGraph",)
    assert "ProofGraph" in boundary_doc
    assert "Product-only state must stay outside `comp` artifacts." in boundary_doc


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
    assert "Product facade response observations" in product_map
    assert "touch_log is lab-only diagnostic" in lab_readme
    assert "product_facade_verification_bundle.v0" in lab_readme
    assert "not a stable wire contract" in lab_readme
    assert "native production authority engine" in lab_readme


def _artifact_lifecycle_boundary() -> str:
    return Path("docs/architecture/contracts/artifact-lifecycle-boundary.md").read_text(
        encoding="utf-8"
    )


def _run_lifecycle_lab_observations():
    runtime = ProductFacadeRuntime()
    canonical_run = runtime.submit(
        ProductInput(
            run_id="run-lifecycle-canonical",
            subject_id="facility-1",
            public_row_id="public-row-lifecycle-canonical",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            values={"amount": 1200, "unit": "kWh"},
            witnesses=_product_witnesses(),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )
    policy_run = runtime.submit_policy_preflight(
        ProductPolicyPreflightInput(
            run_id="run-lifecycle-policy",
            subject_id="facility-1",
            public_row_id="public-row-lifecycle-policy",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            material_id="material:invoice-lifecycle",
            source_ref="invoice.pdf",
            values={"amount": 1200, "unit": "kWh"},
            witnesses=_product_witnesses(),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )
    canonical_public = runtime.publish(canonical_run.run_id)
    policy_public = runtime.publish(policy_run.run_id)
    canonical_audit = runtime.audit(canonical_public.public_row_id)
    policy_audit = runtime.audit(policy_public.public_row_id)

    return {
        "canonical_submit": canonical_run.touch_log,
        "policy_submit": policy_run.touch_log,
        "canonical_publish": canonical_public.touch_log,
        "policy_publish": policy_public.touch_log,
        "canonical_audit": canonical_audit.touch_log,
        "policy_audit": policy_audit.touch_log,
    }


def _product_witnesses() -> tuple[ProductWitness, ...]:
    return (
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
    )


def _publish_canonical_runtime(runtime: ProductFacadeRuntime, run_id: str):
    run = runtime.submit(
        ProductInput(
            run_id=run_id,
            subject_id="facility-1",
            public_row_id=f"public-row-{run_id}",
            projection_id="public-row",
            projection_fields=("amount", "unit"),
            values={"amount": 1200, "unit": "kWh"},
            witnesses=_product_witnesses(),
            known_fields=frozenset({"amount", "unit"}),
            allowed_units=frozenset({"kWh"}),
        )
    )
    return runtime.publish(run.run_id)


def _assert_contract_mentions(
    boundary_doc: str,
    transition: str,
    artifact_names: tuple[str, ...],
) -> None:
    assert transition in boundary_doc
    for artifact_name in artifact_names:
        assert f"`{artifact_name}`" in boundary_doc
