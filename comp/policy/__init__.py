"""Pre-validation policy boundary vocabulary.

This package models policy-side descriptors and effects. It must remain
non-authoritative: policy vocabulary can shape validation handoff, but it does
not validate claims, authorize public projection, or replay receipts.
"""

from comp.policy.boundary import (
    PIPELINE_SCOPES,
    POLICY_EFFECT_KINDS,
    MaterialDescriptor,
    PipelineScope,
    PolicyEffect,
    PolicyEffectKind,
)

__all__ = [
    "PIPELINE_SCOPES",
    "POLICY_EFFECT_KINDS",
    "MaterialDescriptor",
    "PipelineScope",
    "PolicyEffect",
    "PolicyEffectKind",
]
