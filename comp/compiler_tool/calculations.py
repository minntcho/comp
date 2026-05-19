from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CalculationStep:
    step_id: str
    operation: str
    input_ids: tuple[str, ...] = field(default_factory=tuple)
    output_value: Any = None
    output_unit: str | None = None


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
class DerivedClaim:
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


__all__ = [
    "CalculationStep",
    "CalculationTrace",
    "DerivedClaim",
]
