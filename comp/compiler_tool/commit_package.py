from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from comp.compiler_tool.models import CompileReport, Hazard, ProofObligation
from comp.compiler_tool.report_status import recompute_report_status
from comp.judgment.receipts import DependencyFingerprint, ProjectionValueCommitment


@dataclass(frozen=True)
class ReviewPackage:
    package_id: str
    subject_id: str
    report_status: str
    checked_claim_fields: tuple[str, ...] = field(default_factory=tuple)
    checked_claim_witness_ids: tuple[str, ...] = field(default_factory=tuple)
    semantic_judgment_ids: tuple[str, ...] = field(default_factory=tuple)
    reference_binding_ids: tuple[str, ...] = field(default_factory=tuple)
    derived_claim_fields: tuple[str, ...] = field(default_factory=tuple)
    derived_claim_ids: tuple[str, ...] = field(default_factory=tuple)
    calculation_trace_ids: tuple[str, ...] = field(default_factory=tuple)
    formula_ids: tuple[str, ...] = field(default_factory=tuple)
    projection_value_commitments: tuple[ProjectionValueCommitment, ...] = field(
        default_factory=tuple
    )
    dependency_fingerprints: tuple[DependencyFingerprint, ...] = field(
        default_factory=tuple
    )
    open_obligation_ids: tuple[str, ...] = field(default_factory=tuple)
    resolved_obligation_ids: tuple[str, ...] = field(default_factory=tuple)
    hazard_ids: tuple[str, ...] = field(default_factory=tuple)
    profile_id: str | None = None
    complete: bool = False

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


CommitPackage = ReviewPackage


def build_commit_package(
    report: CompileReport,
    *,
    subject_id: str,
    package_id: str | None = None,
    profile_id: str | None = None,
    semantic_judgment_ids: Iterable[str] = (),
    dependency_fingerprints: Iterable[DependencyFingerprint] = (),
) -> ReviewPackage:
    report_status = recompute_report_status(report)
    open_obligation_ids = tuple(
        _obligation_id(obligation) for obligation in report.obligations
    )
    has_open_blocking_obligation = any(
        obligation.blocking for obligation in report.obligations
    )
    hazard_ids = tuple(_hazard_id(hazard) for hazard in report.hazards)

    return ReviewPackage(
        package_id=package_id or f"commit-package:{subject_id}",
        subject_id=subject_id,
        report_status=report_status,
        checked_claim_fields=tuple(claim.field for claim in report.checked_claims),
        checked_claim_witness_ids=tuple(
            claim.witness_id for claim in report.checked_claims
        ),
        semantic_judgment_ids=tuple(semantic_judgment_ids),
        reference_binding_ids=tuple(
            binding.binding_id for binding in report.reference_bindings
        ),
        derived_claim_fields=tuple(claim.field for claim in report.derived_claims),
        derived_claim_ids=tuple(claim.claim_id for claim in report.derived_claims),
        calculation_trace_ids=tuple(
            claim.trace.trace_id for claim in report.derived_claims
        ),
        formula_ids=_unique(claim.formula_id for claim in report.derived_claims),
        projection_value_commitments=_projection_value_commitments(report),
        dependency_fingerprints=tuple(dependency_fingerprints),
        open_obligation_ids=open_obligation_ids,
        resolved_obligation_ids=tuple(
            _obligation_id(obligation)
            for obligation in report.resolved_obligations
        ),
        hazard_ids=hazard_ids,
        profile_id=profile_id,
        complete=report_status == "accepted"
        and not has_open_blocking_obligation
        and not hazard_ids,
    )


def _obligation_id(obligation: ProofObligation) -> str:
    if obligation.obligation_id is not None:
        return obligation.obligation_id
    return _stable_id(
        "proof_obligation",
        obligation.kind,
        obligation.field,
        obligation.reason,
    )


def _hazard_id(hazard: Hazard) -> str:
    return _stable_id("hazard", hazard.kind, hazard.field, hazard.severity)


def _projection_value_commitments(
    report: CompileReport,
) -> tuple[ProjectionValueCommitment, ...]:
    checked = tuple(
        ProjectionValueCommitment.from_value(
            field=claim.field,
            source_kind="checked_claim",
            source_id=_checked_claim_source_id(claim.field, claim.witness_id),
            value=claim.value,
        )
        for claim in report.checked_claims
    )
    derived = tuple(
        ProjectionValueCommitment.from_value(
            field=claim.field,
            source_kind="derived_claim",
            source_id=claim.claim_id,
            value=claim.value,
        )
        for claim in report.derived_claims
    )
    return checked + derived


def _checked_claim_source_id(field: str, witness_id: str) -> str:
    return _stable_id("checked_claim", field, witness_id)


def _stable_id(*parts: str) -> str:
    return ":".join(str(part) for part in parts)


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    seen = set()
    unique_values = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return tuple(unique_values)


__all__ = ["ReviewPackage", "CommitPackage", "build_commit_package"]
