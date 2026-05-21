from __future__ import annotations

from comp.compiler_tool import (
    CalculationFormula,
    CalculationInput,
    ClaimHypothesis,
    CompilerTool,
    DependencyFingerprint,
    EvidenceWitness,
    InterpretationHypothesis,
    ReferenceBinding,
    ReferenceCatalog,
    ReferenceSelectionCriteria,
    apply_calculation_result,
    calculate_derived_claim,
)
from comp.compiler_tool.models import CompileReport, ProofObligation
from comp.scenarios.synthetic.generator import SyntheticRun
from comp.scenarios.synthetic.references import reference_catalog_from_run


class SyntheticPcfAdapter:
    """Turns synthetic raw sources into comp inputs without reading oracle files."""

    projection_fields = ("electricity_kwh", "co2e_kg")

    def __init__(self, run: SyntheticRun):
        self.run = run
        self.config = run.config

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
        return reference_catalog_from_run(self.run)

    def input_claim(self) -> CalculationInput:
        row = self.run.raw_sources.electricity_rows[0]
        return CalculationInput(
            claim_id=self.config.input_claim_id,
            field="electricity_kwh",
            value=row.amount,
            unit=row.unit,
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
                "manifest": self.run.manifest,
            }
        }

    def synthetic_manifest_fingerprint(self) -> DependencyFingerprint:
        return DependencyFingerprint.from_payload(
            dependency_kind="synthetic_manifest",
            dependency_id=(
                f"synthetic_manifest:{self.config.scenario_id}:seed-{self.config.seed}"
            ),
            payload=self.run.manifest,
        )

    def _hypothesis_from_raw(self) -> InterpretationHypothesis:
        row = self.run.raw_sources.electricity_rows[0]
        expected = self.run.oracle.expected_claims[0]
        return InterpretationHypothesis(
            hypothesis_id=self.config.subject_id,
            subject_id=self.config.subject_id,
            claims=(
                ClaimHypothesis(
                    field="electricity_kwh",
                    value=row.amount,
                    witness_id=expected.witness_id,
                    origin="synthetic_raw_source",
                ),
            ),
            witnesses=(
                EvidenceWitness(
                    witness_id=expected.witness_id,
                    field="electricity_kwh",
                    source=f"raw_sources/{row.source_ref}",
                    span=row.source_row_id,
                    text=f"{row.amount} {row.unit}",
                ),
            ),
        )


__all__ = ["SyntheticPcfAdapter"]
