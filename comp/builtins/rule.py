from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

from comp.builtins.esg import (
    compatible as builtin_compatible,
    dimension as builtin_dimension,
    evidence as builtin_evidence,
    missing as builtin_missing,
    origin as builtin_origin,
    valid as builtin_valid,
    valid_period as builtin_valid_period,
)

if TYPE_CHECKING:
    from comp.eval.rule import RuleEvalContext


@dataclass(frozen=True)
class RuleBuiltinSpec:
    name: str
    arg_modes: tuple[str, ...]
    impl: Callable[..., Any]


def _missing(ctx: RuleEvalContext, role_name: str) -> bool:
    return builtin_missing(role_name, ctx.frame)


def _origin(ctx: RuleEvalContext, role_name: str):
    return builtin_origin(role_name, ctx.frame, ctx.claims_by_id)


def _evidence(ctx: RuleEvalContext, kind: str) -> int:
    return builtin_evidence(kind, ctx.frame, ctx.claims_by_id)


def _dimension(ctx: RuleEvalContext, raw_unit: Any):
    return builtin_dimension(raw_unit, ctx.env)


def _compatible(ctx: RuleEvalContext, activity_type: Any, raw_unit: Any) -> bool:
    return builtin_compatible(activity_type, raw_unit, ctx.env)


def _valid(ctx: RuleEvalContext, value: Any) -> bool:
    return builtin_valid(value, ctx.env)


def _valid_period(ctx: RuleEvalContext, value: Any) -> bool:
    return builtin_valid_period(value)


DEFAULT_RULE_BUILTIN_REGISTRY: dict[str, RuleBuiltinSpec] = {
    "missing": RuleBuiltinSpec(
        name="missing",
        arg_modes=("slot_name",),
        impl=_missing,
    ),
    "origin": RuleBuiltinSpec(
        name="origin",
        arg_modes=("slot_name",),
        impl=_origin,
    ),
    "evidence": RuleBuiltinSpec(
        name="evidence",
        arg_modes=("symbol_name",),
        impl=_evidence,
    ),
    "dimension": RuleBuiltinSpec(
        name="dimension",
        arg_modes=("value",),
        impl=_dimension,
    ),
    "compatible": RuleBuiltinSpec(
        name="compatible",
        arg_modes=("value", "value"),
        impl=_compatible,
    ),
    "valid": RuleBuiltinSpec(
        name="valid",
        arg_modes=("value",),
        impl=_valid,
    ),
    "valid_period": RuleBuiltinSpec(
        name="valid_period",
        arg_modes=("value",),
        impl=_valid_period,
    ),
}


def get_default_rule_builtin_registry() -> dict[str, RuleBuiltinSpec]:
    return dict(DEFAULT_RULE_BUILTIN_REGISTRY)


__all__ = [
    "RuleBuiltinSpec",
    "DEFAULT_RULE_BUILTIN_REGISTRY",
    "get_default_rule_builtin_registry",
]
