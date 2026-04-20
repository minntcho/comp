from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class LexExpr:
    pass


@dataclass
class LexLiteral(LexExpr):
    value: Any


@dataclass
class LexSymbolConst(LexExpr):
    name: str


@dataclass
class LexSetExpr(LexExpr):
    items: list[LexExpr] = field(default_factory=list)


@dataclass
class LexBuiltinCall(LexExpr):
    name: str
    args: list[LexExpr] = field(default_factory=list)


@dataclass
class LexColumnRef(LexExpr):
    column_name: str


@dataclass
class LexContextRef(LexExpr):
    role_name: str


@dataclass
class LexRowLabelMatch(LexExpr):
    label: str


@dataclass
class LexUnion(LexExpr):
    options: list[LexExpr] = field(default_factory=list)
