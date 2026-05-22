import pytest

from comp.compiler_tool import (
    CalculatedClaim,
    CalculationStep,
    CalculationTrace,
    CanonicalReference,
    CheckedClaim,
    CompilerProfile,
    DomainPack,
    EvidenceRef,
    ReferenceCatalog,
    ReferenceCatalogSnapshot,
    ReferenceRecord,
    ValidationReport,
    ValidationRequirement,
    prepare_commit,
    profile_lock_envelope_body,
    reference_catalog_snapshot_fingerprint,
    reference_record_fingerprint,
)
from comp.judgment import PublicOutputSpec
from comp.persistence import (
    ArtifactMaterial,
    InMemoryArtifactStore,
    build_receipt_envelope_set,
    receipt_artifact_refs,
    replay_public_projection,
)
from comp.runtime import (
    CompilerRunArtifactMaterializationError,
    materialize_compiler_run_artifacts,
)


def test_materialize_compiler_run_artifacts_builds_replayable_materials():
    report, preparation, external_bodies = _accepted_compiler_run()

    materials = materialize_compiler_run_artifacts(
        report,
        preparation,
        external_artifact_bodies=external_bodies,
    )
    assert all(isinstance(material, ArtifactMaterial) for material in materials)
    assert {
        (material.artifact_kind, material.artifact_id) for material in materials
    } == {
        (ref.artifact_kind, ref.artifact_id)
        for ref in receipt_artifact_refs(preparation.receipt)
    }

    envelopes = build_receipt_envelope_set(preparation.receipt, materials)
    store = InMemoryArtifactStore()
    for envelope in envelopes:
        store.record(envelope)

    replay = replay_public_projection(
        {"amount": 1200, "co2e_emission": 0.48},
        PublicOutputSpec("public-row", ("amount", "co2e_emission")),
        receipt=preparation.receipt,
        artifacts=store,
    )

    assert replay.public_row == {"amount": 1200, "co2e_emission": 0.48}


def test_materialize_compiler_run_artifacts_requires_receipt():
    report = ValidationReport(
        status="accepted",
        validation_requirements=(
            ValidationRequirement(
                kind="reference_selection_required",
                field="co2e_emission",
                reason="ambiguous",
                requirement_id="reference-selection:hyp-1:co2e_emission",
            ),
        ),
    )
    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
    )

    with pytest.raises(CompilerRunArtifactMaterializationError, match="receipt"):
        materialize_compiler_run_artifacts(report, preparation)


def test_materialize_compiler_run_artifacts_requires_external_dependency_body():
    report, preparation, external_bodies = _accepted_compiler_run()
    missing_reference_record = {
        key: body
        for key, body in external_bodies.items()
        if key != ("reference_record", "factor.kr_grid.2024.location_based")
    }

    with pytest.raises(
        CompilerRunArtifactMaterializationError,
        match="missing external artifact body",
    ):
        materialize_compiler_run_artifacts(
            report,
            preparation,
            external_artifact_bodies=missing_reference_record,
        )


def _accepted_compiler_run():
    profile = CompilerProfile(
        profile_id="pcf-profile",
        domain_packs=(DomainPack(domain_id="pcf", version="2026.1"),),
        projection_policy_id="pcf-public-row.v1",
    )
    profile_body = profile_lock_envelope_body(profile)
    profile_fingerprint = _fingerprint_from_body(profile_body)

    reference_record = ReferenceRecord(
        reference_id="factor.kr_grid.2024.location_based",
        reference_type="emission_factor",
        labels=("KR grid 2024 location based",),
        attributes=(
            ("factor_value", 0.0004),
            ("input_unit", "kWh"),
            ("output_unit", "tCO2e"),
        ),
        source="factor-catalog.csv",
        witness_ids=("ref-factor-row-17",),
    )
    reference_fingerprint = reference_record_fingerprint(reference_record)
    catalog = ReferenceCatalog(records=(reference_record,))
    snapshot = ReferenceCatalogSnapshot.from_catalog(
        catalog,
        catalog_id="fixture-catalog",
        catalog_version="2026.1",
        selected_reference_ids=(reference_record.reference_id,),
    )
    snapshot_fingerprint = reference_catalog_snapshot_fingerprint(snapshot)

    binding = CanonicalReference(
        binding_id="bind-amount-factor",
        claim_id="checked_claim:amount:span-amount",
        reference_id=reference_record.reference_id,
        reference_type="emission_factor",
        selected_candidate_id="candidate:factor",
        selector_rule_id="factor-selector.v1",
        source_witness_ids=("ref-factor-row-17",),
    )
    report = ValidationReport(
        status="accepted",
        evidence_refs=(
            EvidenceRef(
                witness_id="span-amount",
                field="amount",
                source="invoice.pdf",
                span="page=1#xywh=10,10,20,20",
                text="Amount 1200 kWh",
            ),
        ),
        checked_claims=(
            CheckedClaim(
                field="amount",
                value=1200,
                witness_id="span-amount",
                origin="source_text",
            ),
        ),
        canonical_references=(binding,),
        calculated_claims=(
            CalculatedClaim(
                claim_id="hyp-1:co2e_emission",
                field="co2e_emission",
                value=0.48,
                unit="tCO2e",
                trace=CalculationTrace(
                    trace_id="trace:hyp-1:co2e_emission",
                    formula_id="ghg.electricity_factor_multiplication.v1",
                    input_claim_ids=("checked_claim:amount:span-amount",),
                    reference_binding_ids=("bind-amount-factor",),
                    steps=(
                        CalculationStep(
                            step_id="multiply-input-by-factor",
                            operation="multiply",
                            input_ids=(
                                "checked_claim:amount:span-amount",
                                "bind-amount-factor",
                            ),
                            output_value=0.48,
                            output_unit="tCO2e",
                        ),
                    ),
                ),
            ),
        ),
    )
    preparation = prepare_commit(
        report,
        subject_id="facility-1",
        public_row_id="public-row-1",
        projection_id="public-row",
        profile_id=profile.profile_id,
        dependency_fingerprints=(
            profile_fingerprint,
            reference_fingerprint,
            snapshot_fingerprint,
        ),
    )

    external_bodies = {
        ("compiler_profile", profile.profile_id): profile_body,
        (
            "reference_record",
            reference_record.reference_id,
        ): _reference_record_body(reference_record, reference_fingerprint),
        (
            "reference_catalog_snapshot",
            snapshot.snapshot_id,
        ): _catalog_snapshot_body(snapshot, snapshot_fingerprint),
    }
    return report, preparation, external_bodies


def _fingerprint_from_body(body):
    from comp.compiler_tool import DependencyFingerprint

    return DependencyFingerprint(
        dependency_kind=body["dependency_kind"],
        dependency_id=body["dependency_id"],
        fingerprint=body["fingerprint"],
        digest_alg=body["digest_alg"],
    )


def _dependency_fingerprint_body(fingerprint):
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _reference_record_body(record, fingerprint):
    return {
        **_dependency_fingerprint_body(fingerprint),
        "reference_id": record.reference_id,
        "reference_type": record.reference_type,
        "labels": record.labels,
        "attributes": record.attributes,
        "source": record.source,
        "witness_ids": record.witness_ids,
    }


def _catalog_snapshot_body(snapshot, fingerprint):
    return {
        **_dependency_fingerprint_body(fingerprint),
        "snapshot_id": snapshot.snapshot_id,
        "catalog_id": snapshot.catalog_id,
        "catalog_version": snapshot.catalog_version,
        "record_fingerprints": tuple(
            _dependency_fingerprint_body(record_fingerprint)
            for record_fingerprint in snapshot.record_fingerprints
        ),
    }
