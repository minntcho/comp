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


def test_scoped_grant_records_pipeline_access_without_projection_authority():
    from comp.policy import ScopedGrant

    grant = ScopedGrant(
        grant_id="grant:fuel_used:selection",
        subject_id="material:fuel_used",
        scope="selection_evaluation",
        basis="observed source attribute",
        conditions=(("requires_review", False),),
        retention="decision_audit",
    )

    assert grant.grant_id == "grant:fuel_used:selection"
    assert grant.subject_id == "material:fuel_used"
    assert grant.scope == "selection_evaluation"
    assert grant.basis == "observed source attribute"
    assert grant.conditions == (("requires_review", False),)
    assert grant.retention == "decision_audit"
    assert grant.authorizes_public_projection is False

    projection_candidate = ScopedGrant(
        grant_id="grant:fuel_used:projection-candidate",
        subject_id="decision:fuel_used->amount",
        scope="projection_candidate",
        basis="selected for later receipt consideration",
    )

    assert projection_candidate.scope == "projection_candidate"
    assert projection_candidate.authorizes_public_projection is False

    with pytest.raises(ValueError, match="unknown pipeline scope"):
        ScopedGrant(
            grant_id="grant:public",
            subject_id="material:fuel_used",
            scope="public_projection",
            basis="not allowed",
        )


def test_selection_decision_requires_grant_for_validation_handoff():
    from comp.policy import ScopedGrant, SelectionDecision

    selected_without_grant = SelectionDecision(
        decision_id="decision:fuel_used->amount",
        subject_id="material:fuel_used",
        status="selected",
        basis="declared alias",
        target_id="field:amount",
    )

    assert selected_without_grant.status == "selected"
    assert selected_without_grant.allows_scope("validation_handoff") is False
    assert selected_without_grant.authorizes_public_projection is False

    handoff_grant = ScopedGrant(
        grant_id="grant:fuel_used:validation-handoff",
        subject_id="decision:fuel_used->amount",
        scope="validation_handoff",
        basis="declared alias selected",
    )
    selected_with_grant = SelectionDecision(
        decision_id="decision:fuel_used->amount",
        subject_id="material:fuel_used",
        status="selected",
        basis="declared alias",
        target_id="field:amount",
        grants=(handoff_grant,),
        denied_scopes=("projection_candidate",),
    )

    assert selected_with_grant.allows_scope("validation_handoff") is True
    assert selected_with_grant.allows_scope("projection_candidate") is False
    assert selected_with_grant.authorizes_public_projection is False

    with pytest.raises(ValueError, match="unknown selection status"):
        SelectionDecision(
            decision_id="decision:validated",
            subject_id="material:fuel_used",
            status="validated",
            basis="not allowed",
        )


def test_decision_ledger_lists_grants_and_validation_handoff_subjects():
    from comp.policy import (
        DecisionLedger,
        MaterialDescriptor,
        PolicyEffect,
        ScopedGrant,
        SelectionDecision,
    )

    descriptor = MaterialDescriptor(
        material_id="material:fuel_used",
        material_kind="source_attribute",
        field_knownness="unknown",
    )
    effect = PolicyEffect(
        effect_id="effect:select:fuel_used",
        effect_kind="select",
        subject_id="material:fuel_used",
        basis="declared alias",
        scope="validation_handoff",
    )
    grant = ScopedGrant(
        grant_id="grant:fuel_used:validation-handoff",
        subject_id="decision:fuel_used->amount",
        scope="validation_handoff",
        basis="declared alias selected",
    )
    decision = SelectionDecision(
        decision_id="decision:fuel_used->amount",
        subject_id="material:fuel_used",
        status="selected",
        basis="declared alias",
        target_id="field:amount",
        grants=(grant,),
    )
    ledger = DecisionLedger(
        ledger_id="ledger:run-1",
        policy_profile_id="profile:strict-public",
        descriptors=(descriptor,),
        effects=(effect,),
        decisions=(decision,),
    )

    assert ledger.decision_for("decision:fuel_used->amount") == decision
    assert ledger.grants_for("decision:fuel_used->amount") == (grant,)
    assert ledger.grants_for("decision:fuel_used->amount", scope="validation_handoff") == (
        grant,
    )
    assert ledger.selected_validation_decision_ids() == (
        "decision:fuel_used->amount",
    )
    assert ledger.authorizes_public_projection is False


def test_policy_package_does_not_expose_projection_or_replay_authority():
    import comp.policy as policy

    for name in (
        "PublicOutputReceipt",
        "build_public_output",
        "build_public_output_receipt",
        "replay_public_projection",
    ):
        assert not hasattr(policy, name)
