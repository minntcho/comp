from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from comp import PublicOutputReceipt, PublicOutputSpec
from comp.judgment.receipts import (
    DependencyFingerprint,
    PublicOutputReceiptCitations,
    PublicOutputValueCommitment,
)
from comp.persistence import ArtifactEnvelope
from examples.product_facade_lab.runtime import (
    CompCompatibleVerificationInput,
    CompVerificationOutput,
    verify_comp_compatible_input,
)


def write_verification_bundle(
    verification_input: CompCompatibleVerificationInput,
    path: str | Path,
) -> Path:
    bundle_path = Path(path)
    bundle = verification_input_to_bundle(verification_input)
    bundle_path.write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return bundle_path


def verify_verification_bundle(
    bundle: Mapping[str, Any],
) -> CompVerificationOutput:
    return verify_comp_compatible_input(verification_input_from_bundle(bundle))


def verify_verification_bundle_file(path: str | Path) -> CompVerificationOutput:
    bundle = json.loads(Path(path).read_text(encoding="utf-8"))
    return verify_verification_bundle(bundle)


def verification_input_to_bundle(
    verification_input: CompCompatibleVerificationInput,
) -> dict[str, object]:
    return {
        "schema_version": "product_facade_verification_bundle.v0",
        "bundle_kind": "comp_compatible_verification_input",
        "public_row_id": verification_input.public_row_id,
        "public_row": _json_value(verification_input.public_row),
        "projection": _public_output_spec_to_mapping(verification_input.projection),
        "receipt_handle": verification_input.receipt_handle,
        "public_output_receipt": _public_output_receipt_to_mapping(
            verification_input.public_output_receipt
        ),
        "artifact_envelopes": [
            _artifact_envelope_to_mapping(envelope)
            for envelope in verification_input.artifact_envelopes
        ],
        "validation_summary": _json_value(verification_input.validation_summary),
        "explanation_hints": _json_value(verification_input.explanation_hints),
        "omitted_verification_outputs": list(
            verification_input.omitted_verification_outputs
        ),
        "product_only_excluded": list(verification_input.product_only_excluded),
    }


def verification_input_from_bundle(
    bundle: Mapping[str, Any],
) -> CompCompatibleVerificationInput:
    if bundle.get("schema_version") != "product_facade_verification_bundle.v0":
        raise ValueError("Unsupported product facade verification bundle version.")
    if bundle.get("bundle_kind") != "comp_compatible_verification_input":
        raise ValueError("Unsupported product facade verification bundle kind.")
    return CompCompatibleVerificationInput(
        public_row_id=str(bundle["public_row_id"]),
        public_row=dict(bundle["public_row"]),
        projection=_public_output_spec_from_mapping(bundle["projection"]),
        public_output_receipt=_public_output_receipt_from_mapping(
            bundle["public_output_receipt"]
        ),
        receipt_handle=str(bundle["receipt_handle"]),
        artifact_envelopes=tuple(
            _artifact_envelope_from_mapping(envelope)
            for envelope in bundle["artifact_envelopes"]
        ),
        validation_summary=dict(bundle["validation_summary"]),
        explanation_hints=_tuple_pairs(bundle.get("explanation_hints", ())),
        omitted_verification_outputs=tuple(
            bundle.get("omitted_verification_outputs", ())
        ),
        product_only_excluded=tuple(bundle.get("product_only_excluded", ())),
    )


def _public_output_spec_to_mapping(spec: PublicOutputSpec) -> dict[str, object]:
    return {
        "projection_id": spec.projection_id,
        "output_fields": list(spec.output_fields),
    }


def _public_output_spec_from_mapping(mapping: Mapping[str, Any]) -> PublicOutputSpec:
    return PublicOutputSpec(
        projection_id=str(mapping["projection_id"]),
        output_fields=tuple(mapping["output_fields"]),
    )


def _public_output_receipt_to_mapping(
    receipt: PublicOutputReceipt,
) -> dict[str, object]:
    return {
        "draft_id": receipt.draft_id,
        "winner_receipt_ids": list(receipt.winner_receipt_ids),
        "barrier_snapshot": _json_value(receipt.barrier_snapshot),
        "public_row_id": receipt.public_row_id,
        "projection_id": receipt.projection_id,
        "authorized_fields": list(receipt.authorized_fields),
        "citations": (
            None
            if receipt.citations is None
            else _receipt_citations_to_mapping(receipt.citations)
        ),
    }


def _public_output_receipt_from_mapping(
    mapping: Mapping[str, Any],
) -> PublicOutputReceipt:
    citations = mapping.get("citations")
    return PublicOutputReceipt(
        draft_id=str(mapping["draft_id"]),
        winner_receipt_ids=tuple(mapping["winner_receipt_ids"]),
        barrier_snapshot=_tuple_pairs(mapping["barrier_snapshot"]),
        public_row_id=str(mapping["public_row_id"]),
        projection_id=str(mapping["projection_id"]),
        authorized_fields=tuple(mapping["authorized_fields"]),
        citations=(
            None
            if citations is None
            else _receipt_citations_from_mapping(citations)
        ),
    )


def _receipt_citations_to_mapping(
    citations: PublicOutputReceiptCitations,
) -> dict[str, object]:
    return {
        "governance_decision_id": citations.governance_decision_id,
        "governance_status": citations.governance_status,
        "governance_reasons": list(citations.governance_reasons),
        "commit_package_id": citations.commit_package_id,
        "commit_package_complete": citations.commit_package_complete,
        "subject_id": citations.subject_id,
        "projection_id": citations.projection_id,
        "authorized_fields": list(citations.authorized_fields),
        "profile_id": citations.profile_id,
        "report_status": citations.report_status,
        "checked_claim_fields": list(citations.checked_claim_fields),
        "checked_claim_witness_ids": list(citations.checked_claim_witness_ids),
        "semantic_judgment_ids": list(citations.semantic_judgment_ids),
        "reference_binding_ids": list(citations.reference_binding_ids),
        "derived_claim_fields": list(citations.derived_claim_fields),
        "derived_claim_ids": list(citations.derived_claim_ids),
        "calculation_trace_ids": list(citations.calculation_trace_ids),
        "formula_ids": list(citations.formula_ids),
        "resolved_obligation_ids": list(citations.resolved_obligation_ids),
        "open_obligation_ids": list(citations.open_obligation_ids),
        "hazard_ids": list(citations.hazard_ids),
        "projection_value_commitments": [
            _value_commitment_to_mapping(commitment)
            for commitment in citations.projection_value_commitments
        ],
        "dependency_fingerprints": [
            _dependency_fingerprint_to_mapping(fingerprint)
            for fingerprint in citations.dependency_fingerprints
        ],
    }


def _receipt_citations_from_mapping(
    mapping: Mapping[str, Any],
) -> PublicOutputReceiptCitations:
    return PublicOutputReceiptCitations(
        governance_decision_id=str(mapping["governance_decision_id"]),
        governance_status=str(mapping["governance_status"]),
        governance_reasons=tuple(mapping["governance_reasons"]),
        commit_package_id=str(mapping["commit_package_id"]),
        commit_package_complete=bool(mapping["commit_package_complete"]),
        subject_id=str(mapping["subject_id"]),
        projection_id=str(mapping["projection_id"]),
        authorized_fields=tuple(mapping["authorized_fields"]),
        profile_id=mapping["profile_id"],
        report_status=str(mapping["report_status"]),
        checked_claim_fields=tuple(mapping["checked_claim_fields"]),
        checked_claim_witness_ids=tuple(mapping["checked_claim_witness_ids"]),
        semantic_judgment_ids=tuple(mapping["semantic_judgment_ids"]),
        reference_binding_ids=tuple(mapping["reference_binding_ids"]),
        derived_claim_fields=tuple(mapping["derived_claim_fields"]),
        derived_claim_ids=tuple(mapping["derived_claim_ids"]),
        calculation_trace_ids=tuple(mapping["calculation_trace_ids"]),
        formula_ids=tuple(mapping["formula_ids"]),
        resolved_obligation_ids=tuple(mapping["resolved_obligation_ids"]),
        open_obligation_ids=tuple(mapping["open_obligation_ids"]),
        hazard_ids=tuple(mapping["hazard_ids"]),
        projection_value_commitments=tuple(
            _value_commitment_from_mapping(commitment)
            for commitment in mapping["projection_value_commitments"]
        ),
        dependency_fingerprints=tuple(
            _dependency_fingerprint_from_mapping(fingerprint)
            for fingerprint in mapping["dependency_fingerprints"]
        ),
    )


def _value_commitment_to_mapping(
    commitment: PublicOutputValueCommitment,
) -> dict[str, str]:
    return {
        "field": commitment.field,
        "source_kind": commitment.source_kind,
        "source_id": commitment.source_id,
        "value_digest": commitment.value_digest,
        "digest_alg": commitment.digest_alg,
    }


def _value_commitment_from_mapping(
    mapping: Mapping[str, Any],
) -> PublicOutputValueCommitment:
    return PublicOutputValueCommitment(
        field=str(mapping["field"]),
        source_kind=str(mapping["source_kind"]),
        source_id=str(mapping["source_id"]),
        value_digest=str(mapping["value_digest"]),
        digest_alg=str(mapping["digest_alg"]),
    )


def _dependency_fingerprint_to_mapping(
    fingerprint: DependencyFingerprint,
) -> dict[str, str]:
    return {
        "dependency_kind": fingerprint.dependency_kind,
        "dependency_id": fingerprint.dependency_id,
        "fingerprint": fingerprint.fingerprint,
        "digest_alg": fingerprint.digest_alg,
    }


def _dependency_fingerprint_from_mapping(
    mapping: Mapping[str, Any],
) -> DependencyFingerprint:
    return DependencyFingerprint(
        dependency_kind=str(mapping["dependency_kind"]),
        dependency_id=str(mapping["dependency_id"]),
        fingerprint=str(mapping["fingerprint"]),
        digest_alg=str(mapping["digest_alg"]),
    )


def _artifact_envelope_to_mapping(envelope: ArtifactEnvelope) -> dict[str, object]:
    return {
        "artifact_id": envelope.artifact_id,
        "artifact_kind": envelope.artifact_kind,
        "schema_version": envelope.schema_version,
        "body_digest": envelope.body_digest,
        "body": _json_value(envelope.body, preserve_tuples=True),
        "source_refs": list(envelope.source_refs),
        "meta": _json_value(envelope.meta, preserve_tuples=True),
    }


def _artifact_envelope_from_mapping(mapping: Mapping[str, Any]) -> ArtifactEnvelope:
    return ArtifactEnvelope(
        artifact_id=str(mapping["artifact_id"]),
        artifact_kind=str(mapping["artifact_kind"]),
        schema_version=str(mapping["schema_version"]),
        body_digest=str(mapping["body_digest"]),
        body=dict(_restore_json_value(mapping["body"])),
        source_refs=tuple(mapping.get("source_refs", ())),
        meta=_tuple_pairs(_restore_json_value(mapping.get("meta", ()))),
    )


def _tuple_pairs(values: Any) -> tuple[tuple[str, Any], ...]:
    return tuple((str(key), value) for key, value in values)


def _json_value(value: Any, *, preserve_tuples: bool = False) -> Any:
    if isinstance(value, PublicOutputValueCommitment):
        return _value_commitment_to_mapping(value)
    if isinstance(value, DependencyFingerprint):
        return _dependency_fingerprint_to_mapping(value)
    if isinstance(value, Mapping):
        return {
            str(key): _json_value(item, preserve_tuples=preserve_tuples)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        items = [_json_value(item, preserve_tuples=preserve_tuples) for item in value]
        if preserve_tuples:
            return {"__tuple__": items}
        return items
    if isinstance(value, list):
        return [_json_value(item, preserve_tuples=preserve_tuples) for item in value]
    return value


def _restore_json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        if set(value) == {"__tuple__"}:
            return tuple(_restore_json_value(item) for item in value["__tuple__"])
        return {str(key): _restore_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_restore_json_value(item) for item in value]
    return value


__all__ = [
    "verify_verification_bundle",
    "verify_verification_bundle_file",
    "verification_input_from_bundle",
    "verification_input_to_bundle",
    "write_verification_bundle",
]
