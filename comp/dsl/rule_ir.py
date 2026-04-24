from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class RuleExpr:
    pass


@dataclass
class RuleLiteral(RuleExpr):
    value: Any


@dataclass
class LocalVarRef(RuleExpr):
    name: str


@dataclass
class FrameSlotRef(RuleExpr):
    role_name: str


@dataclass
class RowFieldRef(RuleExpr):
    field_name: str


@dataclass
class ContextValueRef(RuleExpr):
    role_name: str


@dataclass
class PolicyRef(RuleExpr):
    key: str


@dataclass
class HasDiagnostic(RuleExpr):
    severity: str
    code: str


@dataclass
class HasApproval(RuleExpr):
    key: str


@dataclass
class SymbolConst(RuleExpr):
    name: str


@dataclass
class RuleBuiltinCall(RuleExpr):
    name: str
    args: list[RuleExpr] = field(default_factory=list)


@dataclass
class RuleSetExpr(RuleExpr):
    items: list[RuleExpr] = field(default_factory=list)


@dataclass
class RuleCoalesce(RuleExpr):
    options: list[RuleExpr] = field(default_factory=list)


@dataclass
class RuleUnary(RuleExpr):
    op: str
    operand: RuleExpr


@dataclass
class RuleBinary(RuleExpr):
    left: RuleExpr
    op: str
    right: RuleExpr


__all__ = [
    "RuleExpr",
    "RuleLiteral",
    "LocalVarRef",
    "FrameSlotRef",
    "RowFieldRef",
    "ContextValueRef",
    "PolicyRef",
    "HasDiagnostic",
    "HasApproval",
    "SymbolConst",
    "RuleBuiltinCall",
    "RuleSetExpr",
    "RuleCoalesce",
    "RuleUnary",
    "RuleBinary",
]
