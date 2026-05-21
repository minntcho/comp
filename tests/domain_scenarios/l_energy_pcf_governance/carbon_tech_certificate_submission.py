from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from comp import ProjectionSpec, SubjectRef, project_public_row
from comp.compiler_tool import (
    CalculationStep,
    CalculationTrace,
    CheckedClaim,
    CompileReport,
    DerivedClaim,
    EvidenceWitness,
    ProofObligation,
    ReferenceBinding,
    prepare_commit,
    with_recomputed_status,
)
from tests.domain_scenarios.core import (
    ScenarioContract,
    ScenarioDefinition,
    SourceRef,
    build_domain_scenario_result,
)


SCENARIO_ID = "l_energy.carbon_tech_certificate_submission.v1"
PROJECTION_ID = "l-energy-carbon-tech-certificate-submission"
PROJECTION_FIELDS = (
    "actor_id",
    "submission_type",
    "certificate_boundary",
    "dqr",
    "carbon_tech_final_emission_tco2e",
)
EXPECTED_PROJECTION = {
    "actor_id": "carbon_tech",
    "submission_type": "certificate",
    "certificate_boundary": "Cradle-to-Gate",
    "dqr": "Medium",
    "carbon_tech_final_emission_tco2e": 13390,
}

SOURCE_CASE_ID = "001-l-energy-pcf-governance"
SOURCE_COMMIT = "618c44dfcea1ee1e235550776acb78d8f20a7e0c"
SUBJECT_ID = "case:001-l-energy-pcf-governance:carbon-tech-certificate"
PUBLIC_ROW_ID = "public-row:carbon-tech-certificate-submission"

FORMULA_ID = "pcf.carbon_tech_certificate_factor.v1"
CERTIFICATE_FACTOR_BINDING_ID = "bind:carbon-tech:certificate_factor"
FINAL_EMISSION_CLAIM_ID = "carbon-tech:final_emission_tco2e"
CERTIFICATE_BOUNDARY_OBLIGATION_ID = (
    "carbon-tech:certificate_boundary:supports_cradle_to_gate"
)

ACTOR_ID = "carbon_tech"
SUBMISSION_TYPE = "certificate"
CERTIFICATE_BOUNDARY = "Cradle-to-Gate"
DQR = "Medium"
ACTIVITY_INPUT_MODE = "certificate_only"
PRODUCTION_TON = 8250
CERTIFICATE_FACTOR_TCO2E_PER_TON = Decimal("1.623")

RESOLVER_STEPS = (
    "load_platform_carbon_tech_certificate_fixture",
    "verify_certificate_boundary_context",
    "bind_certificate_factor",
    "calculate_certificate_emission",
    "prepare_commit",
    "receipt_gated_projection",
)

SOURCE_REFS = (
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="docs/e2e/cases/001-l-energy-pcf-governance.md",
    ),
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="docs/e2e/dummy-data-mapping-l-energy-pcf.md",
    ),
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
    ),
    SourceRef(
        repo="minntcho/esg-platform",
        commit=SOURCE_COMMIT,
        path="tests/e2e/expected/001-l-energy-pcf-governance.receipt.json",
    ),
)


def run_carbon_tech_certificate_submission_scenario():
    report = carbon_tech_certificate_submission_report()
    preparation = prepare_commit(
        report,
        subject_id=SUBJECT_ID,
        public_row_id=PUBLIC_ROW_ID,
        projection_id=PROJECTION_ID,
    )
    projection = None
    if preparation.receipt is not None:
        projection = project_public_row(
            _projection_source(report),
            ProjectionSpec(PROJECTION_ID, PROJECTION_FIELDS),
            receipt=preparation.receipt,
        )
    return build_domain_scenario_result(
        scenario_id=SCENARIO_ID,
        report=report,
        preparation=preparation,
        projection=projection,
        subject=SubjectRef("claim", SUBJECT_ID),
        resolver_steps=RESOLVER_STEPS,
    )


def carbon_tech_certificate_submission_report() -> CompileReport:
    return with_recomputed_status(
        CompileReport(
            status="accepted",
            evidence_witnesses=_evidence_witnesses(),
            checked_claims=_checked_claims(),
            resolved_obligations=_resolved_obligations(),
            reference_bindings=_reference_bindings(),
            derived_claims=_derived_claims(),
            can_project_public_row=True,
        )
    )


def _evidence_witnesses() -> tuple[EvidenceWitness, ...]:
    return (
        EvidenceWitness(
            witness_id="source:carbon-tech-certificate-metadata",
            field="certificate_boundary",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.carbon_tech.certificate.boundary",
            text="Cradle-to-Gate",
        ),
        EvidenceWitness(
            witness_id="source:carbon-tech-certificate-factor",
            field="certificate_factor_tco2e_per_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.carbon_tech.certificate.factor",
            text="1.623 tCO2e/ton",
        ),
        EvidenceWitness(
            witness_id="source:carbon-tech-production",
            field="production_ton",
            source="tests/e2e/cases/001-l-energy-pcf-governance.yaml",
            span="data_setup.carbon_tech.production_ton",
            text="8,250 ton",
        ),
    )


def _checked_claims() -> tuple[CheckedClaim, ...]:
    return (
        CheckedClaim(
            "actor_id",
            ACTOR_ID,
            "source:carbon-tech-certificate-metadata",
            "platform_fixture",
        ),
        CheckedClaim(
            "submission_type",
            SUBMISSION_TYPE,
            "source:carbon-tech-certificate-metadata",
            "certificate_submission",
        ),
        CheckedClaim(
            "activity_input_mode",
            ACTIVITY_INPUT_MODE,
            "source:carbon-tech-certificate-metadata",
            "certificate_submission",
        ),
        CheckedClaim(
            "certificate_boundary",
            CERTIFICATE_BOUNDARY,
            "source:carbon-tech-certificate-metadata",
            "certificate_submission",
        ),
        CheckedClaim(
            "dqr",
            DQR,
            "source:carbon-tech-certificate-metadata",
            "certificate_submission",
        ),
        CheckedClaim(
            "production_ton",
            PRODUCTION_TON,
            "source:carbon-tech-production",
            "certificate_submission",
        ),
    )


def _resolved_obligations() -> tuple[ProofObligation, ...]:
    return (
        ProofObligation(
            kind="certificate_boundary_supported",
            field="certificate_boundary",
            reason="supports_cradle_to_gate",
            obligation_id=CERTIFICATE_BOUNDARY_OBLIGATION_ID,
        ),
    )


def _reference_bindings() -> tuple[ReferenceBinding, ...]:
    return (
        ReferenceBinding(
            binding_id=CERTIFICATE_FACTOR_BINDING_ID,
            claim_id=SCENARIO_ID,
            reference_id="platform.factor.carbon_tech_certificate_per_ton",
            reference_type="certificate_factor",
            selector_rule_id="platform.expected_receipt.fixture",
            source_witness_ids=("source:carbon-tech-certificate-factor",),
        ),
    )


def _derived_claims() -> tuple[DerivedClaim, ...]:
    raw_emission = Decimal(PRODUCTION_TON) * CERTIFICATE_FACTOR_TCO2E_PER_TON
    final_emission = _round_half_up(raw_emission)
    return (
        DerivedClaim(
            claim_id=FINAL_EMISSION_CLAIM_ID,
            field="carbon_tech_final_emission_tco2e",
            value=final_emission,
            unit="tCO2e",
            origin="certificate_factor_calculated",
            trace=CalculationTrace(
                trace_id=f"trace:{FINAL_EMISSION_CLAIM_ID}",
                formula_id=FORMULA_ID,
                input_claim_ids=("production_ton",),
                reference_binding_ids=(CERTIFICATE_FACTOR_BINDING_ID,),
                steps=(
                    CalculationStep(
                        step_id="certificate-emission-raw-tco2e",
                        operation="multiply",
                        input_ids=("production_ton", CERTIFICATE_FACTOR_BINDING_ID),
                        output_value=_number(raw_emission),
                        output_unit="tCO2e",
                    ),
                    CalculationStep(
                        step_id="rounded-certificate-emission-tco2e",
                        operation="round",
                        input_ids=("certificate-emission-raw-tco2e",),
                        output_value=final_emission,
                        output_unit="tCO2e",
                    ),
                ),
            ),
        ),
    )


def _projection_source(report: CompileReport) -> dict[str, object]:
    values = {claim.field: claim.value for claim in report.checked_claims}
    values.update({claim.field: claim.value for claim in report.derived_claims})
    return values


def _round_half_up(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


CARBON_TECH_CERTIFICATE_SCENARIO = ScenarioDefinition(
    scenario_id=SCENARIO_ID,
    title="Carbon Tech certificate submission",
    run=run_carbon_tech_certificate_submission_scenario,
    source_refs=SOURCE_REFS,
    contract=ScenarioContract(
        must_commit=True,
        required_projection=EXPECTED_PROJECTION,
        required_resolved_obligation_kinds=("certificate_boundary_supported",),
        required_reference_binding_ids=(CERTIFICATE_FACTOR_BINDING_ID,),
        required_derived_claim_ids=(FINAL_EMISSION_CLAIM_ID,),
        required_receipt_reference_binding_ids=(CERTIFICATE_FACTOR_BINDING_ID,),
        required_receipt_derived_claim_ids=(FINAL_EMISSION_CLAIM_ID,),
        required_receipt_calculation_trace_ids=(
            f"trace:{FINAL_EMISSION_CLAIM_ID}",
        ),
        required_receipt_formula_ids=(FORMULA_ID,),
    ),
)


__all__ = [
    "CARBON_TECH_CERTIFICATE_SCENARIO",
    "CERTIFICATE_BOUNDARY_OBLIGATION_ID",
    "CERTIFICATE_FACTOR_BINDING_ID",
    "EXPECTED_PROJECTION",
    "FINAL_EMISSION_CLAIM_ID",
    "PROJECTION_FIELDS",
    "PROJECTION_ID",
    "SCENARIO_ID",
    "carbon_tech_certificate_submission_report",
    "run_carbon_tech_certificate_submission_scenario",
]
