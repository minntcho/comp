import pytest


def test_material_descriptor_captures_pre_validation_metadata():
    from comp.policy import MaterialDescriptor

    descriptor = MaterialDescriptor(
        material_id="material:fuel_used",
        material_kind="source_attribute",
        field_knownness="unknown",
        risk_tier="medium",
        projection_sensitivity="public_possible",
        evidence_availability="context_only",
        source_ref="source:invoice-1",
        attributes=(
            ("raw_field", "fuel_used"),
            ("raw_value", 1200),
        ),
    )

    assert descriptor.material_id == "material:fuel_used"
    assert descriptor.material_kind == "source_attribute"
    assert descriptor.field_knownness == "unknown"
    assert descriptor.risk_tier == "medium"
    assert descriptor.projection_sensitivity == "public_possible"
    assert descriptor.evidence_availability == "context_only"
    assert descriptor.source_ref == "source:invoice-1"
    assert descriptor.attributes == (
        ("raw_field", "fuel_used"),
        ("raw_value", 1200),
    )


def test_policy_effect_records_scope_and_basis_without_authority():
    from comp.policy import (
        PIPELINE_SCOPES,
        POLICY_EFFECT_KINDS,
        PipelineScope,
        PolicyEffect,
        PolicyEffectKind,
    )

    effect = PolicyEffect(
        effect_id="effect:hold:fuel_used",
        effect_kind="hold",
        subject_id="material:fuel_used",
        basis="unit evidence required",
        scope="selection_evaluation",
        reason="missing unit witness",
        payload=(("required_evidence", "unit_witness"),),
    )

    assert "hold" in POLICY_EFFECT_KINDS
    assert "validation_handoff" in PIPELINE_SCOPES
    assert effect.effect_kind == "hold"
    assert effect.scope == "selection_evaluation"
    assert effect.basis == "unit evidence required"
    assert effect.payload == (("required_evidence", "unit_witness"),)
    assert PipelineScope is not None
    assert PolicyEffectKind is not None


def test_policy_vocabulary_rejects_authority_shaped_effects_and_scopes():
    from comp.policy import PolicyEffect

    with pytest.raises(ValueError, match="unknown policy effect kind"):
        PolicyEffect(
            effect_id="effect:authorize",
            effect_kind="authorize_public_projection",
            subject_id="material:fuel_used",
            basis="not allowed",
        )

    with pytest.raises(ValueError, match="unknown pipeline scope"):
        PolicyEffect(
            effect_id="effect:public",
            effect_kind="grant_scope",
            subject_id="material:fuel_used",
            basis="not allowed",
            scope="public_projection",
        )

    with pytest.raises(ValueError, match="scope is required"):
        PolicyEffect(
            effect_id="effect:grant",
            effect_kind="grant_scope",
            subject_id="material:fuel_used",
            basis="selection allowed",
        )


def test_policy_package_does_not_expose_projection_or_replay_authority():
    import comp.policy as policy

    for name in (
        "PublicOutputReceipt",
        "build_public_output",
        "build_public_output_receipt",
        "replay_public_projection",
    ):
        assert not hasattr(policy, name)
