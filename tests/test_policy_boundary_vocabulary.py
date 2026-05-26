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


def test_selected_validation_contract_freezes_handoff_decisions_from_ledger():
    from comp.policy import (
        DecisionLedger,
        ScopedGrant,
        SelectionDecision,
        SelectedValidationContract,
    )

    handoff_grant = ScopedGrant(
        grant_id="grant:plant:validation-handoff",
        subject_id="decision:plant->site",
        scope="validation_handoff",
        basis="declared alias selected",
    )
    projection_candidate_grant = ScopedGrant(
        grant_id="grant:fuel_used:projection-candidate",
        subject_id="decision:fuel_used->amount",
        scope="projection_candidate",
        basis="eligible for later receipt consideration",
    )
    selected_for_handoff = SelectionDecision(
        decision_id="decision:plant->site",
        subject_id="material:plant",
        status="selected",
        basis="declared alias",
        target_id="field:site",
        grants=(handoff_grant,),
    )
    selected_for_projection_consideration = SelectionDecision(
        decision_id="decision:fuel_used->amount",
        subject_id="material:fuel_used",
        status="selected",
        basis="embedding proposal retained for later receipt consideration",
        target_id="field:amount",
        grants=(projection_candidate_grant,),
    )
    held_handoff_candidate = SelectionDecision(
        decision_id="decision:supplier_code->supplier_id",
        subject_id="material:supplier_code",
        status="held",
        basis="review required",
        target_id="field:supplier_id",
        grants=(
            ScopedGrant(
                grant_id="grant:supplier_code:validation-handoff",
                subject_id="decision:supplier_code->supplier_id",
                scope="validation_handoff",
                basis="blocked until reviewer approval",
            ),
        ),
    )
    ledger = DecisionLedger(
        ledger_id="ledger:run-1",
        policy_profile_id="profile:strict-public",
        decisions=(
            selected_for_handoff,
            selected_for_projection_consideration,
            held_handoff_candidate,
        ),
    )

    contract = SelectedValidationContract.from_ledger(
        contract_id="selected-contract:run-1",
        ledger=ledger,
        basis="policy resolver finalized validation handoff",
        ledger_digest="digest:ledger-run-1",
    )

    assert contract.contract_id == "selected-contract:run-1"
    assert contract.policy_profile_id == "profile:strict-public"
    assert contract.ledger_id == "ledger:run-1"
    assert contract.ledger_digest == "digest:ledger-run-1"
    assert contract.selected_decision_ids == ("decision:plant->site",)
    assert contract.projection_candidate_decision_ids == (
        "decision:fuel_used->amount",
    )
    assert contract.allows_validation_decision("decision:plant->site") is True
    assert contract.allows_validation_decision("decision:fuel_used->amount") is False
    assert contract.authorizes_public_projection is False


def test_selected_validation_contract_rejects_authority_shaped_scopes():
    from comp.policy import SelectedValidationContract

    with pytest.raises(ValueError, match="unknown pipeline scope"):
        SelectedValidationContract(
            contract_id="selected-contract:public",
            policy_profile_id="profile:strict-public",
            ledger_id="ledger:run-1",
            basis="not allowed",
            validation_scopes=("public_projection",),
        )

    with pytest.raises(ValueError, match="not a validation scope"):
        SelectedValidationContract(
            contract_id="selected-contract:projection",
            policy_profile_id="profile:strict-public",
            ledger_id="ledger:run-1",
            basis="not allowed",
            validation_scopes=("projection_candidate",),
        )

    with pytest.raises(ValueError, match="duplicate selected decision id"):
        SelectedValidationContract(
            contract_id="selected-contract:duplicate",
            policy_profile_id="profile:strict-public",
            ledger_id="ledger:run-1",
            basis="duplicate handoff",
            selected_decision_ids=(
                "decision:plant->site",
                "decision:plant->site",
            ),
        )


def test_conflict_resolver_holds_selected_candidate_when_restricted_by_policy():
    from comp.policy import ConflictResolver, PolicyEffect

    resolver = ConflictResolver()
    decision = resolver.resolve_decision(
        decision_id="decision:fuel_used->amount",
        subject_id="material:fuel_used",
        target_id="field:amount",
        effects=(
            PolicyEffect(
                effect_id="effect:select:fuel_used",
                effect_kind="select",
                subject_id="material:fuel_used",
                basis="embedding score 0.96",
                scope="validation_handoff",
            ),
            PolicyEffect(
                effect_id="effect:grant:fuel_used:validation-handoff",
                effect_kind="grant_scope",
                subject_id="material:fuel_used",
                basis="candidate passed selection threshold",
                scope="validation_handoff",
            ),
            PolicyEffect(
                effect_id="effect:hold:fuel_used",
                effect_kind="hold",
                subject_id="material:fuel_used",
                basis="unit evidence required",
                reason="missing unit witness",
            ),
            PolicyEffect(
                effect_id="effect:restrict:fuel_used:validation-handoff",
                effect_kind="restrict_scope",
                subject_id="material:fuel_used",
                basis="evidence required before compiler handoff",
                scope="validation_handoff",
            ),
        ),
    )

    assert decision.status == "held"
    assert decision.basis == "unit evidence required"
    assert decision.target_id == "field:amount"
    assert decision.grants == ()
    assert decision.denied_scopes == ("validation_handoff",)
    assert decision.allows_scope("validation_handoff") is False
    assert decision.authorizes_public_projection is False


def test_conflict_resolver_turns_scope_grants_into_non_authority_grants():
    from comp.policy import ConflictResolver, PolicyEffect

    decision = ConflictResolver().resolve_decision(
        decision_id="decision:plant->site",
        subject_id="material:plant",
        target_id="field:site",
        effects=(
            PolicyEffect(
                effect_id="effect:select:plant",
                effect_kind="select",
                subject_id="material:plant",
                basis="declared alias",
            ),
            PolicyEffect(
                effect_id="effect:grant:plant:validation-handoff",
                effect_kind="grant_scope",
                subject_id="material:plant",
                basis="declared alias selected",
                scope="validation_handoff",
                payload=(("retention", "validation_audit"),),
            ),
            PolicyEffect(
                effect_id="effect:grant:plant:projection-candidate",
                effect_kind="grant_scope",
                subject_id="material:plant",
                basis="eligible for later receipt consideration",
                scope="projection_candidate",
            ),
        ),
    )

    assert decision.status == "selected"
    assert decision.basis == "declared alias"
    assert tuple(grant.scope for grant in decision.grants) == (
        "validation_handoff",
        "projection_candidate",
    )
    assert decision.grants[0].grant_id == "grant:decision:plant->site:validation_handoff"
    assert decision.grants[0].subject_id == "decision:plant->site"
    assert decision.grants[0].retention == "validation_audit"
    assert decision.allows_scope("validation_handoff") is True
    assert decision.allows_scope("projection_candidate") is True
    assert decision.authorizes_public_projection is False
    assert all(grant.authorizes_public_projection is False for grant in decision.grants)


def test_conflict_resolver_rejects_authority_shaped_or_cross_subject_resolution():
    from comp.policy import ConflictResolver, PolicyEffect

    resolver = ConflictResolver()

    with pytest.raises(ValueError, match="no selection status effect"):
        resolver.resolve_decision(
            decision_id="decision:fuel_used->amount",
            subject_id="material:fuel_used",
            effects=(
                PolicyEffect(
                    effect_id="effect:grant:fuel_used:validation-handoff",
                    effect_kind="grant_scope",
                    subject_id="material:fuel_used",
                    basis="grant without status",
                    scope="validation_handoff",
                ),
            ),
        )

    with pytest.raises(ValueError, match="effect subject mismatch"):
        resolver.resolve_decision(
            decision_id="decision:fuel_used->amount",
            subject_id="material:fuel_used",
            effects=(
                PolicyEffect(
                    effect_id="effect:select:other",
                    effect_kind="select",
                    subject_id="material:other",
                    basis="wrong subject",
                ),
            ),
        )


def test_policy_assembly_builds_decision_ledger_from_subject_effects():
    from comp.policy import (
        MaterialDescriptor,
        PolicyAssembly,
        PolicyAssemblySubject,
        PolicyEffect,
        SelectedValidationContract,
    )

    fuel_descriptor = MaterialDescriptor(
        material_id="material:fuel_used",
        material_kind="source_attribute",
        field_knownness="unknown",
        risk_tier="medium",
    )
    plant_descriptor = MaterialDescriptor(
        material_id="material:plant",
        material_kind="source_attribute",
        field_knownness="declared_alias",
        risk_tier="low",
    )
    effects = (
        PolicyEffect(
            effect_id="effect:select:plant",
            effect_kind="select",
            subject_id="material:plant",
            basis="declared alias",
        ),
        PolicyEffect(
            effect_id="effect:grant:plant:validation-handoff",
            effect_kind="grant_scope",
            subject_id="material:plant",
            basis="declared alias selected",
            scope="validation_handoff",
        ),
        PolicyEffect(
            effect_id="effect:select:fuel_used",
            effect_kind="select",
            subject_id="material:fuel_used",
            basis="embedding score 0.96",
        ),
        PolicyEffect(
            effect_id="effect:hold:fuel_used",
            effect_kind="hold",
            subject_id="material:fuel_used",
            basis="unit evidence required",
        ),
        PolicyEffect(
            effect_id="effect:restrict:fuel_used:validation-handoff",
            effect_kind="restrict_scope",
            subject_id="material:fuel_used",
            basis="evidence required before compiler handoff",
            scope="validation_handoff",
        ),
    )

    assembly = PolicyAssembly(policy_profile_id="profile:strict-public")
    ledger = assembly.assemble_ledger(
        ledger_id="ledger:run-1",
        descriptors=(fuel_descriptor, plant_descriptor),
        effects=effects,
        subjects=(
            PolicyAssemblySubject(
                decision_id="decision:plant->site",
                subject_id="material:plant",
                target_id="field:site",
            ),
            PolicyAssemblySubject(
                decision_id="decision:fuel_used->amount",
                subject_id="material:fuel_used",
                target_id="field:amount",
            ),
        ),
        meta=(("run_id", "run-1"),),
    )

    assert ledger.ledger_id == "ledger:run-1"
    assert ledger.policy_profile_id == "profile:strict-public"
    assert ledger.descriptors == (fuel_descriptor, plant_descriptor)
    assert ledger.effects == effects
    assert ledger.meta == (("run_id", "run-1"),)
    assert tuple(decision.decision_id for decision in ledger.decisions) == (
        "decision:plant->site",
        "decision:fuel_used->amount",
    )

    plant_decision = ledger.decision_for("decision:plant->site")
    fuel_decision = ledger.decision_for("decision:fuel_used->amount")

    assert plant_decision is not None
    assert plant_decision.status == "selected"
    assert plant_decision.allows_scope("validation_handoff") is True
    assert fuel_decision is not None
    assert fuel_decision.status == "held"
    assert fuel_decision.allows_scope("validation_handoff") is False
    assert ledger.selected_validation_decision_ids() == ("decision:plant->site",)
    assert assembly.authorizes_public_projection is False

    contract = SelectedValidationContract.from_ledger(
        contract_id="selected-contract:run-1",
        ledger=ledger,
        basis="assembly finalized validation handoff",
    )

    assert contract.selected_decision_ids == ("decision:plant->site",)
    assert contract.authorizes_public_projection is False


def test_policy_assembly_builds_selected_contract_with_ledger():
    from comp.policy import PolicyAssembly, PolicyAssemblySubject, PolicyEffect

    effects = (
        PolicyEffect(
            effect_id="effect:select:plant",
            effect_kind="select",
            subject_id="material:plant",
            basis="declared alias",
        ),
        PolicyEffect(
            effect_id="effect:grant:plant:validation-handoff",
            effect_kind="grant_scope",
            subject_id="material:plant",
            basis="declared alias selected",
            scope="validation_handoff",
        ),
        PolicyEffect(
            effect_id="effect:grant:plant:projection-candidate",
            effect_kind="grant_scope",
            subject_id="material:plant",
            basis="eligible for later receipt consideration",
            scope="projection_candidate",
        ),
        PolicyEffect(
            effect_id="effect:select:fuel_used",
            effect_kind="select",
            subject_id="material:fuel_used",
            basis="embedding score 0.96",
        ),
        PolicyEffect(
            effect_id="effect:hold:fuel_used",
            effect_kind="hold",
            subject_id="material:fuel_used",
            basis="unit evidence required",
        ),
    )

    ledger, contract = PolicyAssembly(
        policy_profile_id="profile:strict-public",
    ).assemble_selected_validation_contract(
        ledger_id="ledger:run-1",
        contract_id="selected-contract:run-1",
        contract_basis="assembly finalized validation handoff",
        ledger_digest="digest:ledger-run-1",
        effects=effects,
        subjects=(
            PolicyAssemblySubject(
                decision_id="decision:plant->site",
                subject_id="material:plant",
                target_id="field:site",
            ),
            PolicyAssemblySubject(
                decision_id="decision:fuel_used->amount",
                subject_id="material:fuel_used",
                target_id="field:amount",
            ),
        ),
        ledger_meta=(("run_id", "run-1"),),
        contract_meta=(("assembly_id", "assembly:run-1"),),
    )

    assert ledger.ledger_id == "ledger:run-1"
    assert tuple(decision.status for decision in ledger.decisions) == (
        "selected",
        "held",
    )
    assert contract.contract_id == "selected-contract:run-1"
    assert contract.policy_profile_id == "profile:strict-public"
    assert contract.ledger_id == "ledger:run-1"
    assert contract.ledger_digest == "digest:ledger-run-1"
    assert contract.basis == "assembly finalized validation handoff"
    assert contract.selected_decision_ids == ("decision:plant->site",)
    assert contract.projection_candidate_decision_ids == ("decision:plant->site",)
    assert contract.meta == (("assembly_id", "assembly:run-1"),)
    assert contract.authorizes_public_projection is False
    assert ledger.authorizes_public_projection is False


def test_policy_assembly_rejects_unassembled_effects_and_duplicate_subjects():
    from comp.policy import PolicyAssembly, PolicyAssemblySubject, PolicyEffect

    assembly = PolicyAssembly(policy_profile_id="profile:strict-public")

    with pytest.raises(ValueError, match="unassembled policy effect subject"):
        assembly.assemble_ledger(
            ledger_id="ledger:run-1",
            effects=(
                PolicyEffect(
                    effect_id="effect:select:fuel_used",
                    effect_kind="select",
                    subject_id="material:fuel_used",
                    basis="declared alias",
                ),
            ),
            subjects=(
                PolicyAssemblySubject(
                    decision_id="decision:plant->site",
                    subject_id="material:plant",
                ),
            ),
        )

    with pytest.raises(ValueError, match="duplicate policy assembly decision id"):
        assembly.assemble_ledger(
            ledger_id="ledger:run-1",
            effects=(
                PolicyEffect(
                    effect_id="effect:select:plant",
                    effect_kind="select",
                    subject_id="material:plant",
                    basis="declared alias",
                ),
            ),
            subjects=(
                PolicyAssemblySubject(
                    decision_id="decision:plant->site",
                    subject_id="material:plant",
                ),
                PolicyAssemblySubject(
                    decision_id="decision:plant->site",
                    subject_id="material:plant-alias",
                ),
            ),
        )

    with pytest.raises(ValueError, match="no policy effects for assembly subject"):
        assembly.assemble_ledger(
            ledger_id="ledger:run-1",
            effects=(),
            subjects=(
                PolicyAssemblySubject(
                    decision_id="decision:plant->site",
                    subject_id="material:plant",
                ),
            ),
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
