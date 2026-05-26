from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

from comp import PublicOutputSpec, build_public_output
from comp.compiler_tool import (
    ClaimCandidate,
    CompilerTool,
    CommitPreparation,
    EvidenceRef,
    InterpretationHypothesis,
    ValidationReport,
    prepare_commit,
)
from comp.persistence import (
    InMemoryArtifactStore,
    ProjectionReplayReport,
    build_receipt_envelope_set,
    replay_public_projection,
)
from comp.runtime import materialize_compiler_run_artifacts

ProductRunStatus = Literal["publishable", "needs_evidence", "blocked"]


@dataclass(frozen=True)
class ProductWitness:
    field: str
    source: str
    span: str
    text: str = ""

    @property
    def witness_id(self) -> str:
        return f"witness:{self.field}"


@dataclass(frozen=True)
class ProductInput:
    run_id: str
    subject_id: str
    public_row_id: str
    projection_id: str
    projection_fields: tuple[str, ...]
    values: Mapping[str, Any]
    witnesses: tuple[ProductWitness, ...]
    known_fields: frozenset[str]
    allowed_units: frozenset[str] = frozenset()


@dataclass(frozen=True)
class ArtifactTouchLog:
    flow: str
    operation: str
    sync_required: tuple[str, ...] = ()
    sync_required_if_publishing: tuple[str, ...] = ()
    deferred: tuple[str, ...] = ()
    not_used: tuple[str, ...] = ()
    product_only: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "flow": self.flow,
            "operation": self.operation,
            "sync_required": list(self.sync_required),
            "sync_required_if_publishing": list(self.sync_required_if_publishing),
            "deferred": list(self.deferred),
            "not_used": list(self.not_used),
            "product_only": list(self.product_only),
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ProductRun:
    run_id: str
    public_row_id: str
    status: ProductRunStatus
    required_actions: tuple[str, ...]
    touch_log: ArtifactTouchLog


@dataclass(frozen=True)
class ProductPublicRow:
    run_id: str
    public_row_id: str
    public_row: dict[str, Any]
    touch_log: ArtifactTouchLog


@dataclass(frozen=True)
class ProductAudit:
    public_row_id: str
    replay_report: ProjectionReplayReport
    artifact_count: int
    touch_log: ArtifactTouchLog


@dataclass
class _RunRecord:
    product_input: ProductInput
    projection: PublicOutputSpec
    report: ValidationReport
    preparation: CommitPreparation | None = None
    public_row: dict[str, Any] | None = None


class ProductFacadeRuntime:
    """Small comp-backed lab for observing product-shaped submit/publish/audit."""

    def __init__(self) -> None:
        self._runs: dict[str, _RunRecord] = {}
        self._public_row_to_run: dict[str, str] = {}

    def submit(self, product_input: ProductInput) -> ProductRun:
        hypothesis = _canonical_hypothesis(product_input)
        report = CompilerTool(
            known_fields=product_input.known_fields,
            allowed_units=product_input.allowed_units,
        ).compile_interpretation(hypothesis)
        projection = PublicOutputSpec(
            product_input.projection_id,
            product_input.projection_fields,
        )
        self._runs[product_input.run_id] = _RunRecord(
            product_input=product_input,
            projection=projection,
            report=report,
        )
        status = _product_status(report)
        return ProductRun(
            run_id=product_input.run_id,
            public_row_id=product_input.public_row_id,
            status=status,
            required_actions=_required_actions(report),
            touch_log=_submit_touch_log(product_input),
        )

    def publish(self, run_id: str) -> ProductPublicRow:
        record = self._runs[run_id]
        preparation = prepare_commit(
            record.report,
            subject_id=record.product_input.subject_id,
            public_row_id=record.product_input.public_row_id,
            projection_id=record.product_input.projection_id,
        )
        if preparation.receipt is None:
            raise RuntimeError("Product facade publish requires a receipt.")
        source_row = _projection_source(record.report)
        public_row = build_public_output(
            source_row,
            record.projection,
            receipt=preparation.receipt,
        )
        record.preparation = preparation
        record.public_row = public_row
        self._public_row_to_run[record.product_input.public_row_id] = run_id
        return ProductPublicRow(
            run_id=run_id,
            public_row_id=record.product_input.public_row_id,
            public_row=public_row,
            touch_log=_publish_touch_log(),
        )

    def audit(self, public_row_id: str) -> ProductAudit:
        run_id = self._public_row_to_run[public_row_id]
        record = self._runs[run_id]
        if record.preparation is None or record.preparation.receipt is None:
            raise RuntimeError("Product facade audit requires a published receipt.")
        if record.public_row is None:
            raise RuntimeError("Product facade audit requires a public row.")
        materials = materialize_compiler_run_artifacts(
            record.report,
            record.preparation,
        )
        artifact_store = InMemoryArtifactStore()
        envelopes = build_receipt_envelope_set(
            record.preparation.receipt,
            materials,
            record_to=artifact_store,
        )
        replay_report = replay_public_projection(
            record.public_row,
            record.projection,
            receipt=record.preparation.receipt,
            artifacts=artifact_store,
        )
        return ProductAudit(
            public_row_id=public_row_id,
            replay_report=replay_report,
            artifact_count=len(envelopes),
            touch_log=_audit_touch_log(),
        )


def _canonical_hypothesis(product_input: ProductInput) -> InterpretationHypothesis:
    witnesses = tuple(
        EvidenceRef(
            witness_id=witness.witness_id,
            field=witness.field,
            source=witness.source,
            span=witness.span,
            text=witness.text,
        )
        for witness in product_input.witnesses
    )
    return InterpretationHypothesis(
        hypothesis_id=product_input.run_id,
        subject_id=product_input.subject_id,
        claims=tuple(
            ClaimCandidate(
                field=field,
                value=value,
                witness_id=f"witness:{field}",
                origin="product_facade_canonical_input",
            )
            for field, value in product_input.values.items()
        ),
        witnesses=witnesses,
    )


def _product_status(report: ValidationReport) -> ProductRunStatus:
    if report.status == "accepted":
        return "publishable"
    if report.validation_requirements:
        return "needs_evidence"
    return "blocked"


def _required_actions(report: ValidationReport) -> tuple[str, ...]:
    return tuple(
        f"{requirement.kind}:{requirement.field}:{requirement.reason}"
        for requirement in report.validation_requirements
    )


def _projection_source(report: ValidationReport) -> dict[str, Any]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.calculated_claims})
    return values


def _submit_touch_log(product_input: ProductInput) -> ArtifactTouchLog:
    return ArtifactTouchLog(
        flow="canonical_fast_path",
        operation="submit",
        sync_required=("InterpretationHypothesis", "ValidationReport"),
        sync_required_if_publishing=("PublicOutputReceipt",),
        deferred=("ArtifactEnvelope", "ProjectionReplayReport"),
        not_used=(
            "DecisionLedger",
            "SelectedValidationContract",
            "ValidationHandoff",
        ),
        product_only=("ProductInput",),
        notes=(
            "Canonical input had grounded witnesses and known field/unit coverage.",
            f"Projection fields: {', '.join(product_input.projection_fields)}",
        ),
    )


def _publish_touch_log() -> ArtifactTouchLog:
    return ArtifactTouchLog(
        flow="canonical_fast_path",
        operation="publish",
        sync_required=(
            "ValidationReport",
            "ReviewPackage",
            "ReviewDecision",
            "PublicOutputReceipt",
            "PublicOutputSpec",
        ),
        deferred=("ArtifactEnvelope", "ProjectionReplayReport"),
        not_used=(
            "DecisionLedger",
            "SelectedValidationContract",
            "ValidationHandoff",
        ),
    )


def _audit_touch_log() -> ArtifactTouchLog:
    return ArtifactTouchLog(
        flow="canonical_fast_path",
        operation="audit",
        sync_required=("ArtifactEnvelope", "ProjectionReplayReport"),
        not_used=("ProofGraph",),
    )


__all__ = [
    "ArtifactTouchLog",
    "ProductAudit",
    "ProductFacadeRuntime",
    "ProductInput",
    "ProductPublicRow",
    "ProductRun",
    "ProductWitness",
]
