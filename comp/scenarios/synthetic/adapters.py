from __future__ import annotations

from dataclasses import replace

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    CheckedClaim,
    ClaimCandidate,
    CompilerTool,
    DependencyFingerprint,
    EvidenceRef,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    CanonicalReference,
    ReferenceCatalog,
    ReferenceSelectionCriteria,
    with_recomputed_status,
    apply_calculation_result,
    calculate_derived_claim,
)
from comp.compiler_tool.models import ValidationReport, ValidationRequirement
from comp.scenarios.synthetic.models import (
    SYNTHETIC_SOURCE_INPUT_KIND,
    SyntheticInputBundle,
    SyntheticLoadedSource,
    SyntheticResolutionArtifact,
)
from comp.scenarios.synthetic.sources import (
    synthetic_source_input_dependency_id,
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

    def query_for_requirement(self, obligation: ValidationRequirement) -> str | None:
        if obligation.kind != "reference_search_required":
            return None
        return f"{self.config.geography} grid electricity factor {self.config.reporting_period}"

    def blocked_report(self) -> ValidationReport:
        report = CompilerTool(
            known_fields=frozenset({"electricity_kwh"}),
        ).compile_interpretation(self._hypothesis_from_raw())
        result = calculate_derived_claim(
            output_claim_id=self.config.output_claim_id,
            input_claim=self.input_claim(),
            reference_binding=CanonicalReference(
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

    def resolution_seed_report(self) -> ValidationReport:
        report = self.blocked_report()
        resolved_validation_requirements = self._resolved_unit_obligations()
        if not resolved_validation_requirements:
            return report
        return with_recomputed_status(
            replace(
                report,
                resolved_validation_requirements=(
                    *report.resolved_validation_requirements,
                    *resolved_validation_requirements,
                ),
                can_build_public_output=False,
            )
        )

    def anomaly_report(self) -> ValidationReport:
        witnesses: list[EvidenceRef] = []
        checked: list[CheckedClaim] = []
        failed: list[FailedClaim] = []
        obligations: list[ValidationRequirement] = []
        hazards: list[Hazard] = []

        for row in self.input_bundle.raw_sources.electricity_rows:
            amount_witness_id = f"witness:{row.source_row_id}:electricity_kwh"
            witnesses.append(
                EvidenceRef(
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
                    ValidationRequirement(
                        kind="investigate_activity_amount",
                        field="electricity_kwh",
                        reason="negative_amount",
                        requirement_id="synthetic-obligation:negative_amount",
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
                    ValidationRequirement(
                        kind="find_source_witness",
                        field="unit",
                        reason="missing_unit",
                        requirement_id="synthetic-obligation:missing_unit",
                    )
                )
                hazards.append(Hazard(kind="missing_unit", field="unit", severity="review"))
            elif row.unit.lower() != self.config.electricity_unit.lower():
                unit_witness_id = f"witness:{row.source_row_id}:unit"
                witnesses.append(
                    EvidenceRef(
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
                    ValidationRequirement(
                        kind="find_source_witness",
                        field="unit",
                        reason="unsupported_unit",
                        requirement_id="synthetic-obligation:wrong_unit",
                    )
                )

            if row.period != self.config.reporting_period:
                obligations.append(
                    ValidationRequirement(
                        kind="find_context",
                        field="period",
                        reason="period_mismatch",
                        requirement_id="synthetic-obligation:period_mismatch",
                    )
                )
                hazards.append(
                    Hazard(kind="period_mismatch", field="period", severity="review")
                )

            if row.site_id != self.config.site_id:
                obligations.append(
                    ValidationRequirement(
                        kind="resolve_site_identity",
                        field="site_id",
                        reason="site_alias",
                        requirement_id="synthetic-obligation:site_alias",
                    )
                )
                hazards.append(Hazard(kind="site_alias", field="site_id", severity="review"))

        return with_recomputed_status(
            ValidationReport(
                status="accepted",
                evidence_refs=tuple(witnesses),
                checked_claims=tuple(checked),
                failed_claims=tuple(failed),
                validation_requirements=tuple(obligations),
                hazards=tuple(hazards),
                can_build_public_output=False,
            )
        )

    def projection_source(self, report: ValidationReport) -> dict[str, object]:
        values = {claim.field: claim.value for claim in report.checked_claims}
        values.update({claim.field: claim.value for claim in report.calculated_claims})
        return values

    def dependency_fingerprints(self) -> tuple[DependencyFingerprint, ...]:
        return (
            self.synthetic_manifest_fingerprint(),
            *self.synthetic_source_fingerprints(),
        )

    def dependency_artifact_bodies(self):
        manifest_fingerprint = self.synthetic_manifest_fingerprint()
        bodies = {
            (
                manifest_fingerprint.dependency_kind,
                manifest_fingerprint.dependency_id,
            ): {
                "dependency_kind": manifest_fingerprint.dependency_kind,
                "dependency_id": manifest_fingerprint.dependency_id,
                "fingerprint": manifest_fingerprint.fingerprint,
                "digest_alg": manifest_fingerprint.digest_alg,
                "manifest": self.input_bundle.manifest,
            }
        }
        for source in self.input_bundle.loaded_sources:
            fingerprint = self.synthetic_source_fingerprint(source)
            bodies[(fingerprint.dependency_kind, fingerprint.dependency_id)] = {
                "dependency_kind": fingerprint.dependency_kind,
                "dependency_id": fingerprint.dependency_id,
                "fingerprint": fingerprint.fingerprint,
                "digest_alg": fingerprint.digest_alg,
                "source": source.to_payload(),
            }
        return bodies

    def synthetic_manifest_fingerprint(self) -> DependencyFingerprint:
        return DependencyFingerprint.from_payload(
            dependency_kind="synthetic_manifest",
            dependency_id=(
                f"synthetic_manifest:{self.config.scenario_id}:seed-{self.config.seed}"
            ),
            payload=self.input_bundle.manifest,
        )

    def synthetic_source_fingerprints(self) -> tuple[DependencyFingerprint, ...]:
        return tuple(
            self.synthetic_source_fingerprint(source)
            for source in self.input_bundle.loaded_sources
        )

    def synthetic_source_fingerprint(
        self,
        source: SyntheticLoadedSource,
    ) -> DependencyFingerprint:
        return DependencyFingerprint.from_payload(
            dependency_kind=SYNTHETIC_SOURCE_INPUT_KIND,
            dependency_id=synthetic_source_input_dependency_id(
                self.config,
                role=source.role,
                source_ref=source.source_ref,
            ),
            payload=source.to_payload(),
        )

    def _hypothesis_from_raw(self) -> InterpretationHypothesis:
        row = self.input_bundle.raw_sources.electricity_rows[0]
        witness_id = f"witness:{row.source_row_id}:electricity_kwh"
        return InterpretationHypothesis(
            hypothesis_id=self.config.subject_id,
            subject_id=self.config.subject_id,
            claims=(
                ClaimCandidate(
                    field="electricity_kwh",
                    value=row.amount,
                    witness_id=witness_id,
                    origin="synthetic_raw_source",
                ),
            ),
            witnesses=(
                EvidenceRef(
                    witness_id=witness_id,
                    field="electricity_kwh",
                    source=f"raw_sources/{row.source_ref}",
                    span=row.source_row_id,
                    text=f"{row.amount} {row.unit}",
                ),
            ),
        )

    def _resolved_unit_obligations(self) -> tuple[ValidationRequirement, ...]:
        return tuple(
            ValidationRequirement(
                kind="find_source_witness",
                field=artifact.field,
                reason="missing_unit",
                requirement_id=artifact.obligation_id,
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
