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
from comp.policy import (
    DecisionLedger,
    MaterialDescriptor,
    PolicyAssembly,
    PolicyAssemblySubject,
    PolicyEffect,
    SelectedValidationContract,
)
from comp.persistence import (
    InMemoryArtifactStore,
    ProjectionReplayReport,
    build_receipt_envelope_set,
    replay_public_projection,
)
from comp.runtime import (
    ValidationHandoff,
    ValidationHandoffClaim,
    materialize_compiler_run_artifacts,
)

ProductRunStatus = Literal["publishable", "needs_evidence", "blocked"]
ProductRunFlow = Literal["canonical_fast_path", "policy_preflight_path"]


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
class ProductPolicyPreflightInput:
    run_id: str
    subject_id: str
    public_row_id: str
    projection_id: str
    projection_fields: tuple[str, ...]
    material_id: str
    source_ref: str
    values: Mapping[str, Any]
    witnesses: tuple[ProductWitness, ...]
    known_fields: frozenset[str]
    allowed_units: frozenset[str] = frozenset()
    policy_profile_id: str = "profile:product-facade-lab"
    material_kind: str = "external_material"


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
    product_input: ProductInput | ProductPolicyPreflightInput
    projection: PublicOutputSpec
    report: ValidationReport
    flow: ProductRunFlow
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
            flow="canonical_fast_path",
        )
        status = _product_status(report)
        return ProductRun(
            run_id=product_input.run_id,
            public_row_id=product_input.public_row_id,
            status=status,
            required_actions=_required_actions(report),
            touch_log=_submit_touch_log(product_input),
        )

    def submit_policy_preflight(
        self,
        product_input: ProductPolicyPreflightInput,
    ) -> ProductRun:
        ledger, contract, handoff = _policy_preflight_handoff(product_input)
        hypothesis = handoff.to_interpretation_hypothesis()
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
            flow="policy_preflight_path",
        )
        status = _product_status(report)
        return ProductRun(
            run_id=product_input.run_id,
            public_row_id=product_input.public_row_id,
            status=status,
            required_actions=_required_actions(report),
            touch_log=_policy_preflight_touch_log(
                product_input,
                ledger_id=ledger.ledger_id,
                contract_id=contract.contract_id,
            ),
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
            touch_log=_publish_touch_log(record.flow),
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
            touch_log=_audit_touch_log(record.flow),
        )


def _canonical_hypothesis(product_input: ProductInput) -> InterpretationHypothesis:
    witnesses = _evidence_refs(product_input.witnesses)
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


def _policy_preflight_handoff(
    product_input: ProductPolicyPreflightInput,
) -> tuple[DecisionLedger, SelectedValidationContract, ValidationHandoff]:
    descriptor = MaterialDescriptor(
        material_id=product_input.material_id,
        material_kind=product_input.material_kind,
        field_knownness="partially_known",
        risk_tier="product_preflight",
        projection_sensitivity="public_candidate",
        evidence_availability="available",
        source_ref=product_input.source_ref,
        attributes=(("observed_fields", tuple(product_input.values.keys())),),
    )
    subjects = tuple(
        PolicyAssemblySubject(
            decision_id=_policy_decision_id(product_input.run_id, field),
            subject_id=_policy_subject_id(product_input.material_id, field),
            target_id=f"field:{field}",
        )
        for field in product_input.values
    )
    effects = tuple(
        effect
        for field in product_input.values
        for effect in (
            PolicyEffect(
                effect_id=f"effect:{product_input.run_id}:{field}:select",
                effect_kind="select",
                subject_id=_policy_subject_id(product_input.material_id, field),
                basis="product facade policy preflight selected field",
            ),
            PolicyEffect(
                effect_id=f"effect:{product_input.run_id}:{field}:handoff",
                effect_kind="grant_scope",
                subject_id=_policy_subject_id(product_input.material_id, field),
                basis="selected external material may enter validation handoff",
                scope="validation_handoff",
            ),
        )
    )
    ledger, contract = PolicyAssembly(
        policy_profile_id=product_input.policy_profile_id,
    ).assemble_selected_validation_contract(
        ledger_id=f"ledger:{product_input.run_id}",
        contract_id=f"selected-contract:{product_input.run_id}",
        contract_basis="product facade policy preflight finalized validation handoff",
        descriptors=(descriptor,),
        effects=effects,
        subjects=subjects,
        ledger_meta=(("run_id", product_input.run_id),),
        contract_meta=(("lab_flow", "policy_preflight_path"),),
    )
    handoff = ValidationHandoff(
        handoff_id=f"handoff:{product_input.run_id}",
        contract=contract,
        hypothesis_id=f"hypothesis:{product_input.run_id}",
        subject_id=product_input.subject_id,
        claims=tuple(
            ValidationHandoffClaim(
                decision_id=_policy_decision_id(product_input.run_id, field),
                claim=ClaimCandidate(
                    field=field,
                    value=value,
                    witness_id=f"witness:{field}",
                    origin="product_facade_policy_preflight",
                ),
            )
            for field, value in product_input.values.items()
        ),
        witnesses=_evidence_refs(product_input.witnesses),
        meta=(("material_id", product_input.material_id),),
    )
    return ledger, contract, handoff


def _evidence_refs(witnesses: tuple[ProductWitness, ...]) -> tuple[EvidenceRef, ...]:
    return tuple(
        EvidenceRef(
            witness_id=witness.witness_id,
            field=witness.field,
            source=witness.source,
            span=witness.span,
            text=witness.text,
        )
        for witness in witnesses
    )


def _policy_subject_id(material_id: str, field: str) -> str:
    return f"{material_id}:{field}"


def _policy_decision_id(run_id: str, field: str) -> str:
    return f"decision:{run_id}:{field}"


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


def _policy_preflight_touch_log(
    product_input: ProductPolicyPreflightInput,
    *,
    ledger_id: str,
    contract_id: str,
) -> ArtifactTouchLog:
    return ArtifactTouchLog(
        flow="policy_preflight_path",
        operation="submit",
        sync_required=(
            "MaterialDescriptor",
            "PolicyEffect",
            "PolicyAssembly",
            "DecisionLedger",
            "SelectedValidationContract",
            "ValidationHandoff",
            "InterpretationHypothesis",
            "ValidationReport",
        ),
        sync_required_if_publishing=("PublicOutputReceipt",),
        deferred=("ArtifactEnvelope", "ProjectionReplayReport"),
        product_only=("ProductPolicyPreflightInput",),
        notes=(
            "Current comp.policy assembly creates DecisionLedger synchronously "
            "before SelectedValidationContract.",
            "Policy preflight shapes compiler-facing input but does not validate "
            "claims or authorize projection.",
            f"Ledger: {ledger_id}",
            f"Contract: {contract_id}",
            f"Material: {product_input.material_id}",
        ),
    )


def _publish_touch_log(flow: ProductRunFlow) -> ArtifactTouchLog:
    not_used = (
        ("DecisionLedger", "SelectedValidationContract", "ValidationHandoff")
        if flow == "canonical_fast_path"
        else ()
    )
    notes = (
        (
            "Policy preflight artifacts were consumed during submit; publish "
            "still depends on receipt-gated projection.",
        )
        if flow == "policy_preflight_path"
        else ()
    )
    return ArtifactTouchLog(
        flow=flow,
        operation="publish",
        sync_required=(
            "ValidationReport",
            "ReviewPackage",
            "ReviewDecision",
            "PublicOutputReceipt",
            "PublicOutputSpec",
        ),
        deferred=("ArtifactEnvelope", "ProjectionReplayReport"),
        not_used=not_used,
        notes=notes,
    )


def _audit_touch_log(flow: ProductRunFlow) -> ArtifactTouchLog:
    return ArtifactTouchLog(
        flow=flow,
        operation="audit",
        sync_required=("ArtifactEnvelope", "ProjectionReplayReport"),
        not_used=("ProofGraph",),
    )


__all__ = [
    "ArtifactTouchLog",
    "ProductAudit",
    "ProductFacadeRuntime",
    "ProductInput",
    "ProductPolicyPreflightInput",
    "ProductPublicRow",
    "ProductRun",
    "ProductWitness",
]
