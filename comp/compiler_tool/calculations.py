from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from numbers import Number
from typing import Any

from comp.compiler_tool.reference_db import ReferenceCatalog, ReferenceLookupError
from comp.compiler_tool.references import ReferenceBinding
from comp.judgment.receipts import DependencyFingerprint


@dataclass(frozen=True)
class CalculationStep:
    step_id: str
    operation: str
    input_ids: tuple[str, ...] = field(default_factory=tuple)
    output_value: Any = None
    output_unit: str | None = None
    exact_output_value: Decimal | None = None
    rounding_quantum: str | None = None
    rounding_mode: str | None = None


@dataclass(frozen=True)
class CalculationTrace:
    trace_id: str
    formula_id: str
    input_claim_ids: tuple[str, ...] = field(default_factory=tuple)
    reference_binding_ids: tuple[str, ...] = field(default_factory=tuple)
    steps: tuple[CalculationStep, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.formula_id:
            raise ValueError("CalculationTrace formula_id is required")


@dataclass(frozen=True)
class CalculatedClaim:
    claim_id: str
    field: str
    value: Any
    unit: str | None
    trace: CalculationTrace
    origin: str = "calculated"

    @property
    def formula_id(self) -> str:
        return self.trace.formula_id

    @property
    def can_authorize_public_projection(self) -> bool:
        return False


DerivedClaim = CalculatedClaim


@dataclass(frozen=True)
class CalculationInput:
    claim_id: str
    field: str
    value: Any
    unit: str | None = None


@dataclass(frozen=True)
class CalculationFormula:
    formula_id: str
    output_field: str
    output_unit: str
    factor_value_attribute: str = "factor_value"
    input_unit_attribute: str = "input_unit"
    output_unit_attribute: str = "output_unit"
    rounding_quantum: str | None = None
    rounding_mode: str = "ROUND_HALF_UP"


@dataclass(frozen=True)
class CalculationRequirement:
    reason: str
    formula_id: str
    output_claim_id: str
    input_claim_id: str | None = None
    reference_binding_id: str | None = None
    reference_id: str | None = None
    expected_unit: str | None = None
    actual_unit: str | None = None
    expected_output_unit: str | None = None
    actual_output_unit: str | None = None
    missing_attribute: str | None = None


@dataclass(frozen=True)
class CalculationResult:
    status: str
    derived_claim: DerivedClaim | None = None
    reason: str | None = None
    requirement: CalculationRequirement | None = None


def calculate_derived_claim(
    *,
    output_claim_id: str,
    input_claim: CalculationInput,
    reference_binding: ReferenceBinding,
    catalog: ReferenceCatalog,
    formula: CalculationFormula,
) -> CalculationResult:
    try:
        reference = catalog.get(reference_binding.reference_id)
    except ReferenceLookupError:
        return _blocked(
            _requirement(
                reason="unknown_reference",
                output_claim_id=output_claim_id,
                input_claim=input_claim,
                reference_binding=reference_binding,
                formula=formula,
            )
        )

    factor_value = reference.attribute(formula.factor_value_attribute)
    if factor_value is None:
        return _blocked(
            _requirement(
                reason="missing_factor_value",
                output_claim_id=output_claim_id,
                input_claim=input_claim,
                reference_binding=reference_binding,
                formula=formula,
                missing_attribute=formula.factor_value_attribute,
            )
        )

    expected_input_unit = reference.attribute(formula.input_unit_attribute)
    if expected_input_unit is not None and input_claim.unit != expected_input_unit:
        return _blocked(
            _requirement(
                reason="unit_mismatch",
                output_claim_id=output_claim_id,
                input_claim=input_claim,
                reference_binding=reference_binding,
                formula=formula,
                expected_unit=expected_input_unit,
                actual_unit=input_claim.unit,
            )
        )

    expected_output_unit = reference.attribute(formula.output_unit_attribute)
    if expected_output_unit is not None and formula.output_unit != expected_output_unit:
        return _blocked(
            _requirement(
                reason="output_unit_mismatch",
                output_claim_id=output_claim_id,
                input_claim=input_claim,
                reference_binding=reference_binding,
                formula=formula,
                expected_output_unit=expected_output_unit,
                actual_output_unit=formula.output_unit,
            )
        )

    input_value = _decimal_number(input_claim.value)
    factor_decimal = _decimal_number(factor_value)
    if input_value is None or factor_decimal is None:
        return _blocked(
            _requirement(
                reason="non_numeric_input",
                output_claim_id=output_claim_id,
                input_claim=input_claim,
                reference_binding=reference_binding,
                formula=formula,
            )
        )

    exact_output_value = _apply_rounding(input_value * factor_decimal, formula)
    output_value = _number(exact_output_value)
    trace = CalculationTrace(
        trace_id=f"trace:{output_claim_id}",
        formula_id=formula.formula_id,
        input_claim_ids=(input_claim.claim_id,),
        reference_binding_ids=(reference_binding.binding_id,),
        steps=(
            CalculationStep(
                step_id="multiply-input-by-factor",
                operation="multiply",
                input_ids=(input_claim.claim_id, reference_binding.binding_id),
                output_value=output_value,
                output_unit=formula.output_unit,
                exact_output_value=exact_output_value,
                rounding_quantum=formula.rounding_quantum,
                rounding_mode=(
                    formula.rounding_mode
                    if formula.rounding_quantum is not None
                    else None
                ),
            ),
        ),
    )
    return CalculationResult(
        status="calculated",
        derived_claim=DerivedClaim(
            claim_id=output_claim_id,
            field=formula.output_field,
            value=output_value,
            unit=formula.output_unit,
            trace=trace,
        ),
    )


def calculation_formula_declaration_fingerprint(
    formula: CalculationFormula,
) -> DependencyFingerprint:
    return DependencyFingerprint.from_payload(
        dependency_kind="calculation_formula",
        dependency_id=f"calculation_formula:{formula.formula_id}",
        payload={
            "formula_id": formula.formula_id,
            "output_field": formula.output_field,
            "output_unit": formula.output_unit,
            "factor_value_attribute": formula.factor_value_attribute,
            "input_unit_attribute": formula.input_unit_attribute,
            "output_unit_attribute": formula.output_unit_attribute,
            "rounding_quantum": formula.rounding_quantum,
            "rounding_mode": formula.rounding_mode,
        },
    )


def _blocked(requirement: CalculationRequirement) -> CalculationResult:
    return CalculationResult(
        status="blocked",
        reason=requirement.reason,
        requirement=requirement,
    )


def _requirement(
    *,
    reason: str,
    output_claim_id: str,
    input_claim: CalculationInput,
    reference_binding: ReferenceBinding,
    formula: CalculationFormula,
    expected_unit: str | None = None,
    actual_unit: str | None = None,
    expected_output_unit: str | None = None,
    actual_output_unit: str | None = None,
    missing_attribute: str | None = None,
) -> CalculationRequirement:
    return CalculationRequirement(
        reason=reason,
        formula_id=formula.formula_id,
        output_claim_id=output_claim_id,
        input_claim_id=input_claim.claim_id,
        reference_binding_id=reference_binding.binding_id,
        reference_id=reference_binding.reference_id,
        expected_unit=expected_unit,
        actual_unit=actual_unit,
        expected_output_unit=expected_output_unit,
        actual_output_unit=actual_output_unit,
        missing_attribute=missing_attribute,
    )


ROUNDING_MODES = {
    "ROUND_HALF_UP": ROUND_HALF_UP,
}


def _decimal_number(value: Any) -> Decimal | None:
    if isinstance(value, bool) or not isinstance(value, Number):
        return None
    try:
        decimal = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not decimal.is_finite():
        return None
    return decimal


def _apply_rounding(value: Decimal, formula: CalculationFormula) -> Decimal:
    if formula.rounding_quantum is None:
        return value
    rounding_mode = ROUNDING_MODES.get(formula.rounding_mode)
    if rounding_mode is None:
        raise ValueError(f"Unsupported rounding mode: {formula.rounding_mode}")
    return value.quantize(Decimal(formula.rounding_quantum), rounding=rounding_mode)


def _number(value: Decimal) -> int | float:
    if value == value.to_integral_value():
        return int(value)
    return float(value)


__all__ = [
    "CalculationStep",
    "CalculationTrace",
    "CalculatedClaim",
    "DerivedClaim",
    "CalculationInput",
    "CalculationFormula",
    "calculation_formula_declaration_fingerprint",
    "CalculationRequirement",
    "CalculationResult",
    "calculate_derived_claim",
]
