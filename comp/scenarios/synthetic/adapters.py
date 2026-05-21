from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CheckedClaim,
    ClaimHypothesis,
    CompilerTool,
    DependencyFingerprint,
    EvidenceWitness,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceSelectionCriteria,
    with_recomputed_status,
    apply_calculation_result,
    calculate_derived_claim,
)
from comp.compiler_tool.models import CompileReport, ProofObligation
from comp.scenarios.synthetic.generator import (
    SyntheticInputBundle,
    SyntheticResolutionArtifact,
)
from comp.scenarios.synthetic.references import reference_catalog_from_input_bundle


class SyntheticPcfAdapter:
    """Turns synthetic raw sources into comp inputs without reading oracle files."""

    projection_fields = ("electricity_kwh", "co2e_kg")

    def __init__(self, input_bundle: SyntheticInputBundle):
        if not isinstance(input_bundle, SyntheticInputBundle):
            raise TypeError("SyntheticPcfAdapter requires a SyntheticInputBundle.")
        self.input_bundle = input_bundle
        self.config = input_bundle.config

    @property
    def subject_id(self) -> str:
        return self.config.subject_id

    @property
    def public_row_id(self) -> str:
        return self.config.public_row_id

    @property
    def projection_id(self) -> str:
        return self.config.projection_id

    @property
    def profile_id(self) -> str:
        return self.config.profile_id

    @property
    def output_claim_id(self) -> str:
        return self.config.output_claim_id

    def reference_catalog(self) -> ReferenceCatalog:
        return reference_catalog_from_input_bundle(self.input_bundle)

    def input_claim(self) -> CalculationInput:
        row = self.input_bundle.raw_sources.electricity_rows[0]
        return CalculationInput(
            claim_id=self.config.input_claim_id,
            field="electricity_kwh",
            value=row.amount,
            unit=row.unit,
        )

    def has_resolution_artifacts(self) -> bool:
        return bool(self.input_bundle.resolution_artifacts.unit_witnesses)

    def resolved_input_claim(self) -> CalculationInput:
        row = self.input_bundle.raw_sources.electricity_rows[0]
        unit_resolution = self._unit_resolution_artifact(row.source_row_id)
        return CalculationInput(
            claim_id=self.config.input_claim_id,
            field="electricity_kwh",
            value=row.amount,
            unit=(
                unit_resolution.resolved_value
                if unit_resolution is not None
                else row.unit
            ),
        )

    def formula(self) -> CalculationFormula:
        return CalculationFormula(
            formula_id=self.config.formula_id,
            output_field="co2e_kg",
            output_unit=self.config.factor_output_unit,
        )

    def reference_selection_criteria(self) -> ReferenceSelectionCriteria:
        return ReferenceSelectionCriteria(
            binding_id=self.config.binding_id,
            claim_id=self.config.input_claim_id,
            reference_type="emission_factor",
            selector_rule_id=self.config.selector_rule_id,
            required_attributes=(
                ("concept_id", "pcf.concept.electricity_consumption"),
                ("geography", self.config.geography),
                ("valid_period", self.config.reporting_period),
                ("method", "location_based"),
            ),
        )

    def query_for_obligation(self, obligation: ProofObligation) -> str | None:
        if obligation.kind != "reference_search_required":
            return None
        return f"{self.config.geography} grid electricity factor {self.config.reporting_period}"

    def blocked_report(self) -> CompileReport:
        report = CompilerTool(
            known_fields=frozenset({"electricity_kwh"}),
        ).compile_interpretation(self._hypothesis_from_raw())
        result = calculate_derived_claim(
            output_claim_id=self.config.output_claim_id,
            input_claim=self.input_claim(),
            reference_binding=ReferenceBinding(
                binding_id=self.config.binding_id,
                claim_id=self.config.input_claim_id,
                reference_id="synthetic.factor.pending",
                reference_type="emission_factor",
            ),
            catalog=ReferenceCatalog(records=()),
            formula=self.formula(),
        )
        return apply_calculation_result(
            report,
            result,
            output_claim_id=self.config.output_claim_id,
            formula=self.formula(),
        )

    def resolution_seed_report(self) -> CompileReport:
        report = self.blocked_report()
        resolved_obligations = self._resolved_unit_obligations()
        if not resolved_obligations:
            return report
        return with_recomputed_status(
            replace(
                report,
                resolved_obligations=(
                    *report.resolved_obligations,
                    *resolved_obligations,
                ),
                can_project_public_row=False,
            )
        )

    def anomaly_report(self) -> CompileReport:
        witnesses: list[EvidenceWitness] = []
        checked: list[CheckedClaim] = []
        failed: list[FailedClaim] = []
        obligations: list[ProofObligation] = []
        hazards: list[Hazard] = []

        for row in self.input_bundle.raw_sources.electricity_rows:
            amount_witness_id = f"witness:{row.source_row_id}:electricity_kwh"
            witnesses.append(
                EvidenceWitness(
                    witness_id=amount_witness_id,
                    field="electricity_kwh",
                    source=f"raw_sources/{row.source_ref}",
                    span=row.source_row_id,
                    text=str(row.amount),
                )
            )
            if float(row.amount) < 0:
                failed.append(
                    FailedClaim(
                        field="electricity_kwh",
                        value=row.amount,
                        reason="negative_amount",
                        origin="synthetic_raw_source",
                        witness_id=amount_witness_id,
                    )
                )
                obligations.append(
                    ProofObligation(
                        kind="investigate_activity_amount",
                        field="electricity_kwh",
                        reason="negative_amount",
                        obligation_id="synthetic-obligation:negative_amount",
                    )
                )
                hazards.append(
                    Hazard(
                        kind="invalid_activity_amount",
                        field="electricity_kwh",
                        severity="block",
                    )
                )
            else:
                checked.append(
                    CheckedClaim(
                        field="electricity_kwh",
                        value=row.amount,
                        witness_id=amount_witness_id,
                        origin="synthetic_raw_source",
                    )
                )

            if not row.unit:
                obligations.append(
                    ProofObligation(
                        kind="find_source_witness",
                        field="unit",
                        reason="missing_unit",
                        obligation_id="synthetic-obligation:missing_unit",
                    )
                )
                hazards.append(Hazard(kind="missing_unit", field="unit", severity="review"))
            elif row.unit.lower() != self.config.electricity_unit.lower():
                unit_witness_id = f"witness:{row.source_row_id}:unit"
                witnesses.append(
                    EvidenceWitness(
                        witness_id=unit_witness_id,
                        field="unit",
                        source=f"raw_sources/{row.source_ref}",
                        span=row.source_row_id,
                        text=row.unit,
                    )
                )
                failed.append(
                    FailedClaim(
                        field="unit",
                        value=row.unit,
                        reason="unsupported_unit",
                        origin="synthetic_raw_source",
                        witness_id=unit_witness_id,
                    )
                )
                obligations.append(
                    ProofObligation(
                        kind="find_source_witness",
                        field="unit",
                        reason="unsupported_unit",
                        obligation_id="synthetic-obligation:wrong_unit",
                    )
                )

            if row.period != self.config.reporting_period:
                obligations.append(
                    ProofObligation(
                        kind="find_context",
                        field="period",
                        reason="period_mismatch",
                        obligation_id="synthetic-obligation:period_mismatch",
                    )
                )
                hazards.append(
                    Hazard(kind="period_mismatch", field="period", severity="review")
                )

            if row.site_id != self.config.site_id:
                obligations.append(
                    ProofObligation(
                        kind="resolve_site_identity",
                        field="site_id",
                        reason="site_alias",
                        obligation_id="synthetic-obligation:site_alias",
                    )
                )
                hazards.append(Hazard(kind="site_alias", field="site_id", severity="review"))

        return with_recomputed_status(
            CompileReport(
                status="accepted",
                evidence_witnesses=tuple(witnesses),
                checked_claims=tuple(checked),
                failed_claims=tuple(failed),
                obligations=tuple(obligations),
                hazards=tuple(hazards),
                can_project_public_row=False,
            )
        )

    def projection_source(self, report: CompileReport) -> dict[str, object]:
        values = {claim.field: claim.value for claim in report.checked_claims}
        values.update({claim.field: claim.value for claim in report.derived_claims})
        return values

    def dependency_fingerprints(self) -> tuple[DependencyFingerprint, ...]:
        return (self.synthetic_manifest_fingerprint(),)

    def dependency_artifact_bodies(self):
        fingerprint = self.synthetic_manifest_fingerprint()
        return {
            (fingerprint.dependency_kind, fingerprint.dependency_id): {
                "dependency_kind": fingerprint.dependency_kind,
                "dependency_id": fingerprint.dependency_id,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
                "manifest": self.input_bundle.manifest,
            }
        }

    def synthetic_manifest_fingerprint(self) -> DependencyFingerprint:
        return DependencyFingerprint.from_payload(
            dependency_kind="synthetic_manifest",
            dependency_id=(
                f"synthetic_manifest:{self.config.scenario_id}:seed-{self.config.seed}"
            ),
            payload=self.input_bundle.manifest,
        )

    def _hypothesis_from_raw(self) -> InterpretationHypothesis:
        row = self.input_bundle.raw_sources.electricity_rows[0]
        witness_id = f"witness:{row.source_row_id}:electricity_kwh"
        return InterpretationHypothesis(
            hypothesis_id=self.config.subject_id,
            subject_id=self.config.subject_id,
            claims=(
                ClaimHypothesis(
                    field="electricity_kwh",
                    value=row.amount,
                    witness_id=witness_id,
                    origin="synthetic_raw_source",
                ),
            ),
            witnesses=(
                EvidenceWitness(
                    witness_id=witness_id,
                    field="electricity_kwh",
                    source=f"raw_sources/{row.source_ref}",
                    span=row.source_row_id,
                    text=f"{row.amount} {row.unit}",
                ),
            ),
        )

    def _resolved_unit_obligations(self) -> tuple[ProofObligation, ...]:
        return tuple(
            ProofObligation(
                kind="find_source_witness",
                field=artifact.field,
                reason="missing_unit",
                obligation_id=artifact.obligation_id,
            )
            for artifact in self.input_bundle.resolution_artifacts.unit_witnesses
            if artifact.field == "unit"
        )

    def _unit_resolution_artifact(
        self,
        source_row_id: str,
    ) -> SyntheticResolutionArtifact | None:
        for artifact in self.input_bundle.resolution_artifacts.unit_witnesses:
            if artifact.source_row_id == source_row_id and artifact.field == "unit":
                return artifact
        return None


__all__ = ["SyntheticPcfAdapter"]
