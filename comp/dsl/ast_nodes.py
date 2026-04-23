from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


class ASTNode:
    pass


class Expr(ASTNode):
    pass


class Statement(ASTNode):
    pass


class ParserAction(ASTNode):
    pass


class ResolverStmt(ASTNode):
    pass


class GovernanceStmt(ASTNode):
    pass


@dataclass
class Program(ASTNode):
    statements: list[Statement] = field(default_factory=list)


@dataclass
class NameExpr(Expr):
    name: str


@dataclass
class LiteralExpr(Expr):
    value: Any


@dataclass
class FunctionCallExpr(Expr):
    name: str
    args: list[Expr] = field(default_factory=list)


@dataclass
class SetExpr(Expr):
    items: list[Expr] = field(default_factory=list)


@dataclass
class ColumnRefExpr(Expr):
    column_name: str


@dataclass
class ContextRefExpr(Expr):
    role_name: str


@dataclass
class RowLabelRefExpr(Expr):
    label: str


@dataclass
class AlternationExpr(Expr):
    options: list[Expr] = field(default_factory=list)


@dataclass
class UnaryExpr(Expr):
    op: str
    operand: Expr


@dataclass
class BinaryExpr(Expr):
    left: Expr
    op: str
    right: Expr


@dataclass
class ModuleDecl(Statement):
    name: str


@dataclass
class ImportDecl(Statement):
    name: str


@dataclass
class DimensionDecl(Statement):
    name: str


@dataclass
class NormalizeClause(ASTNode):
    target_unit: str
    op: str
    factor: float


@dataclass
class UnitDecl(Statement):
    name: str
    dimension: str
    normalize: Optional[NormalizeClause] = None


@dataclass
class ActivityDecl(Statement):
    name: str
    dimension: str
    scope_category: str


@dataclass
class ScopeDecl(Statement):
    chain: list[str]


class ContextStmt(ASTNode):
    pass


@dataclass
class PrecedenceStmt(ContextStmt):
    chain: list[str]


@dataclass
class RefineStmt(ContextStmt):
    specific: str
    broad: str


@dataclass
class TtlStmt(ContextStmt):
    values: list[str]


@dataclass
class SupportsStmt(ContextStmt):
    values: list[str]


@dataclass
class ContextDecl(Statement):
    role_name: str
    statements: list[ContextStmt] = field(default_factory=list)


@dataclass
class TypeRef(ASTNode):
    name: str
    generic: Optional[str] = None


@dataclass
class FieldDecl(ASTNode):
    name: str
    type_ref: TypeRef
    optional: bool = False


@dataclass
class FrameDecl(Statement):
    name: str
    fields: list[FieldDecl] = field(default_factory=list)


@dataclass
class TokenDecl(Statement):
    name: str
    expr: Expr


@dataclass
class FallbackTokenDecl(Statement):
    name: str
    expr: Expr


@dataclass
class BuildStmt(ParserAction):
    frame_name: str


@dataclass
class BindStmt(ParserAction):
    role_name: str
    source_expr: Expr
    optional: bool = False


@dataclass
class ParserInheritStmt(ParserAction):
    role_name: str
    source_expr: Expr
    condition: Optional[Expr] = None


@dataclass
class TagStmt(ParserAction):
    role_name: str
    source_expr: Expr


@dataclass
class ParserDecl(Statement):
    name: str
    source_selectors: list[str]
    actions: list[ParserAction] = field(default_factory=list)


@dataclass
class InheritRule(Statement):
    role_name: str
    source_expr: Expr
    condition: Expr


@dataclass
class InferRule(Statement):
    target_name: str
    op: str
    value_expr: Expr
    condition: Expr
    weight: Optional[float] = None


@dataclass
class RequireRule(Statement):
    condition: Expr


@dataclass
class ForbidRule(Statement):
    condition: Expr
    frame_name: Optional[str] = None


@dataclass
class DiagnosticRule(Statement):
    level: str
    code: str
    condition: Expr


@dataclass
class AssignStmt(ResolverStmt):
    name: str
    value: Expr


@dataclass
class CandidatePoolBlock(ResolverStmt):
    assigns: list[AssignStmt] = field(default_factory=list)


@dataclass
class CommitStmt(ResolverStmt):
    condition: Expr


@dataclass
class ReviewStmt(ResolverStmt):
    condition: Expr


@dataclass
class RejectStmt(ResolverStmt):
    pass


@dataclass
class ResolverDecl(Statement):
    frame_name: str
    statements: list[ResolverStmt] = field(default_factory=list)


@dataclass
class EmitStmt(GovernanceStmt):
    condition: Expr


@dataclass
class MergeStmt(GovernanceStmt):
    condition: Expr


@dataclass
class ForbidMergeStmt(GovernanceStmt):
    condition: Expr


@dataclass
class GovernanceDecl(Statement):
    frame_name: str
    statements: list[GovernanceStmt] = field(default_factory=list)


__all__ = [
    "ASTNode",
    "Expr",
    "Statement",
    "ParserAction",
    "ResolverStmt",
    "GovernanceStmt",
    "Program",
    "NameExpr",
    "LiteralExpr",
    "FunctionCallExpr",
    "SetExpr",
    "ColumnRefExpr",
    "ContextRefExpr",
    "RowLabelRefExpr",
    "AlternationExpr",
    "UnaryExpr",
    "BinaryExpr",
    "ModuleDecl",
    "ImportDecl",
    "DimensionDecl",
    "NormalizeClause",
    "UnitDecl",
    "ActivityDecl",
    "ScopeDecl",
    "ContextStmt",
    "PrecedenceStmt",
    "RefineStmt",
    "TtlStmt",
    "SupportsStmt",
    "ContextDecl",
    "TypeRef",
    "FieldDecl",
    "FrameDecl",
    "TokenDecl",
    "FallbackTokenDecl",
    "BuildStmt",
    "BindStmt",
    "ParserInheritStmt",
    "TagStmt",
    "ParserDecl",
    "InheritRule",
    "InferRule",
    "RequireRule",
    "ForbidRule",
    "DiagnosticRule",
    "AssignStmt",
    "CandidatePoolBlock",
    "CommitStmt",
    "ReviewStmt",
    "RejectStmt",
    "ResolverDecl",
    "EmitStmt",
    "MergeStmt",
    "ForbidMergeStmt",
    "GovernanceDecl",
]
