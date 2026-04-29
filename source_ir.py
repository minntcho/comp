from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SourceCandidate:
    value: Any
    confidence: float
    extraction_mode: str
    source_token_id: Optional[str] = None
    source_fragment_id: Optional[str] = None
    span: Optional[tuple[int, int]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SourceExpr:
    pass


@dataclass
class SourceLiteral(SourceExpr):
    value: Any


@dataclass
class SourceSymbolConst(SourceExpr):
    name: str


@dataclass
class SourceSetExpr(SourceExpr):
    items: list[SourceExpr] = field(default_factory=list)


@dataclass
class SourceBuiltinCall(SourceExpr):
    name: str
    args: list[SourceExpr] = field(default_factory=list)


@dataclass
class SourceTokenRef(SourceExpr):
    token_name: str


@dataclass
class SourceColumnRef(SourceExpr):
    column_name: str


@dataclass
class SourceContextRef(SourceExpr):
    role_name: str


@dataclass
class SourceRowLabelMatch(SourceExpr):
    label: str


@dataclass
class SourceFirstOf(SourceExpr):
    options: list[SourceExpr] = field(default_factory=list)
