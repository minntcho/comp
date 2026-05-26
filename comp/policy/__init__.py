"""Pre-validation policy boundary vocabulary.

This package models policy-side descriptors, effects, scoped grants, selection
decisions, and decision ledgers. It must remain non-authoritative: policy
vocabulary can shape validation handoff, but it does not validate claims,
authorize public projection, or replay receipts.
"""

from comp.policy.boundary import (
    PIPELINE_SCOPES,
    POLICY_EFFECT_KINDS,
    SELECTION_STATUSES,
    ConflictResolver,
    DecisionLedger,
    MaterialDescriptor,
    PipelineScope,
    PolicyAssembly,
    PolicyAssemblySubject,
    PolicyEffect,
    PolicyEffectKind,
    ScopedGrant,
    SelectionDecision,
    SelectionStatus,
    SelectedValidationContract,
)

__all__ = [
    "PIPELINE_SCOPES",
    "POLICY_EFFECT_KINDS",
    "SELECTION_STATUSES",
    "ConflictResolver",
    "DecisionLedger",
    "MaterialDescriptor",
    "PipelineScope",
    "PolicyAssembly",
    "PolicyAssemblySubject",
    "PolicyEffect",
    "PolicyEffectKind",
    "ScopedGrant",
    "SelectionDecision",
    "SelectionStatus",
    "SelectedValidationContract",
]
