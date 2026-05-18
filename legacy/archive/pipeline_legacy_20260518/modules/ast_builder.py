# ast_builder.py
from __future__ import annotations

import ast
from lark import Transformer, Token

from ast_nodes import (
    ActivityDecl,
    AlternationExpr,
    AssignStmt,
    BinaryExpr,
    BindStmt,
    BuildStmt,
    CandidatePoolBlock,
    ColumnRefExpr,
    CommitStmt,
    ContextDecl,
    ContextRefExpr,
    DiagnosticRule,
    DimensionDecl,
    EmitStmt,
    FallbackTokenDecl,
    FieldDecl,
    ForbidMergeStmt,
    ForbidRule,
    FrameDecl,
    FunctionCallExpr,
    GovernanceDecl,
    ImportDecl,
    InheritRule,
    InferRule,
    LiteralExpr,
    MergeStmt,
    ModuleDecl,
    NameExpr,
    NormalizeClause,
    ParserDecl,
    ParserInheritStmt,
    PrecedenceStmt,
    Program,
    RefineStmt,
    RejectStmt,
    RequireRule,
    ResolverDecl,
    ReviewStmt,
    RowLabelRefExpr,
    ScopeDecl,
    SetExpr,
    SupportsStmt,
    TagStmt,
    TokenDecl,
    TtlStmt,
    TypeRef,
    UnaryExpr,
    UnitDecl,
)


class ASTBuilder(Transformer):
    """
    Lark parse tree -> AST dataclasses
    """

    # -----------------------------
    # Tokens
    # -----------------------------
    def IDENT(self, tok: Token):
        return str(tok)

    def NUMBER(self, tok: Token):
        text = str(tok)
        return float(text) if "." in text else int(text)

    def STRING(self, tok: Token):
        return ast.literal_eval(str(tok))

    def BOOL(self, tok: Token):
        return str(tok) == "true"

    def NORM_OP(self, tok: Token):
        return str(tok)

    def INFER_OP(self, tok: Token):
        return str(tok)

    def DIAG_LEVEL(self, tok: Token):
        return str(tok)

    def COMP_OP(self, tok: Token):
        return str(tok)

    # -----------------------------
    # Program
    # -----------------------------
    def program(self, items):
        return Program(statements=list(items))

    # -----------------------------
    # Top-level declarations
    # -----------------------------
    def module_decl(self, items):
        return ModuleDecl(name=items[0])

    def import_decl(self, items):
        return ImportDecl(name=items[0])

    def dimension_decl(self, items):
        return DimensionDecl(name=items[0])

    def normalize_clause(self, items):
        target_unit, op, factor = items
        return NormalizeClause(
            target_unit=target_unit,
            op=op,
            factor=float(factor),
        )

    def unit_decl(self, items):
        name = items[0]
        dimension = items[1]
        normalize = items[2] if len(items) > 2 else None
        return UnitDecl(name=name, dimension=dimension, normalize=normalize)

    def activity_decl(self, items):
        return ActivityDecl(
            name=items[0],
            dimension=items[1],
            scope_category=items[2],
        )

    def scope_chain(self, items):
        return list(items)

    def scope_decl(self, items):
        return ScopeDecl(chain=items[0])

    # -----------------------------
    # Context
    # -----------------------------
    def precedence_chain(self, items):
        return list(items)

    def precedence_stmt(self, items):
        return PrecedenceStmt(chain=items[0])

    def refine_stmt(self, items):
        return RefineStmt(specific=items[0], broad=items[1])

    def ttl_chain(self, items):
        return list(items)

    def ttl_stmt(self, items):
        return TtlStmt(values=items[0])

    def supports_chain(self, items):
        return list(items)

    def supports_stmt(self, items):
        return SupportsStmt(values=items[0])

    def context_decl(self, items):
        role_name = items[0]
        stmts = items[1:]
        return ContextDecl(role_name=role_name, statements=stmts)

    # -----------------------------
    # Frame
    # -----------------------------
    def generic_arg(self, items):
        return items[0]

    def type_ref(self, items):
        name = items[0]
        generic = items[1] if len(items) > 1 else None
        return TypeRef(name=name, generic=generic)

    def optional_marker(self, _items):
        return True

    def field_decl(self, items):
        name = items[0]
        type_ref = items[1]
        optional = bool(items[2]) if len(items) > 2 else False
        return FieldDecl(name=name, type_ref=type_ref, optional=optional)

    def frame_decl(self, items):
        name = items[0]
        fields = items[1:]
        return FrameDecl(name=name, fields=fields)

    # -----------------------------
    # Token declarations
    # -----------------------------
    def token_decl(self, items):
        return TokenDecl(name=items[0], expr=items[1])

    def fallback_token_decl(self, items):
        return FallbackTokenDecl(name=items[0], expr=items[1])

    # -----------------------------
    # Parser declarations
    # -----------------------------
    def selector_chain(self, items):
        return list(items)

    def build_stmt(self, items):
        return BuildStmt(frame_name=items[0])

    def bind_stmt(self, items):
        role_name = items[0]
        if len(items) == 3:
            return BindStmt(role_name=role_name, optional=True, source_expr=items[2])
        return BindStmt(role_name=role_name, optional=False, source_expr=items[1])

    def parser_inherit_stmt(self, items):
        role_name = items[0]
        source_expr = items[1]
        condition = items[2] if len(items) > 2 else None
        return ParserInheritStmt(
            role_name=role_name,
            source_expr=source_expr,
            condition=condition,
        )

    def tag_stmt(self, items):
        return TagStmt(role_name=items[0], source_expr=items[1])

    def parser_decl(self, items):
        name = items[0]
        selectors = items[1]
        actions = items[2:]
        return ParserDecl(name=name, source_selectors=selectors, actions=actions)

    # -----------------------------
    # Rules
    # -----------------------------
    def inherit_rule(self, items):
        return InheritRule(
            role_name=items[0],
            source_expr=items[1],
            condition=items[2],
        )

    def infer_weight(self, items):
        return float(items[0])

    def infer_rule(self, items):
        target_name = items[0]
        op = items[1]
        value_expr = items[2]
        if len(items) == 4:
            weight = None
            condition = items[3]
        else:
            weight = float(items[3])
            condition = items[4]
        return InferRule(
            target_name=target_name,
            op=op,
            value_expr=value_expr,
            weight=weight,
            condition=condition,
        )

    def require_rule(self, items):
        return RequireRule(condition=items[0])

    def forbid_rule(self, items):
        condition = items[0]
        frame_name = items[1] if len(items) > 1 else None
        return ForbidRule(condition=condition, frame_name=frame_name)

    def diagnostic_rule(self, items):
        return DiagnosticRule(
            level=items[0],
            code=items[1],
            condition=items[2],
        )

    # -----------------------------
    # Resolver
    # -----------------------------
    def assign_stmt(self, items):
        return AssignStmt(name=items[0], value=items[1])

    def candidate_pool_block(self, items):
        return CandidatePoolBlock(assigns=list(items))

    def commit_stmt(self, items):
        return CommitStmt(condition=items[0])

    def review_stmt(self, items):
        return ReviewStmt(condition=items[0])

    def reject_stmt(self, _items):
        return RejectStmt()

    def resolver_decl(self, items):
        frame_name = items[0]
        stmts = items[1:]
        return ResolverDecl(frame_name=frame_name, statements=stmts)

    # -----------------------------
    # Governance
    # -----------------------------
    def emit_stmt(self, items):
        return EmitStmt(condition=items[0])

    def merge_stmt(self, items):
        return MergeStmt(condition=items[0])

    def forbid_merge_stmt(self, items):
        return ForbidMergeStmt(condition=items[0])

    def governance_decl(self, items):
        frame_name = items[0]
        stmts = items[1:]
        return GovernanceDecl(frame_name=frame_name, statements=stmts)

    # -----------------------------
    # Expressions
    # -----------------------------
    def qname(self, items):
        return ".".join(items)

    def string_lit(self, items):
        return LiteralExpr(value=items[0])

    def number_lit(self, items):
        return LiteralExpr(value=items[0])

    def bool_lit(self, items):
        return LiteralExpr(value=items[0])

    def function_call(self, items):
        name = items[0]
        args = items[1] if len(items) > 1 else []
        return FunctionCallExpr(name=name, args=args)

    def arg_list(self, items):
        return list(items)

    def set_literal(self, items):
        return SetExpr(items=list(items))

    def column_ref(self, items):
        return ColumnRefExpr(column_name=items[0])

    def context_ref(self, items):
        return ContextRefExpr(role_name=items[0])

    def row_label_ref(self, items):
        return RowLabelRefExpr(label=items[0])

    def source_expr(self, items):
        if len(items) == 1:
            return items[0]
        return AlternationExpr(options=list(items))

    def bool_or(self, items):
        if len(items) == 1:
            return items[0]
        return BinaryExpr(left=items[0], op="or", right=items[1])

    def bool_and(self, items):
        if len(items) == 1:
            return items[0]
        return BinaryExpr(left=items[0], op="and", right=items[1])

    def bool_not(self, items):
        return UnaryExpr(op="not", operand=items[0])

    def grouped_bool(self, items):
        return items[0]

    def comparison(self, items):
        return BinaryExpr(left=items[0], op=items[1], right=items[2])

    def in_expr(self, items):
        return BinaryExpr(left=items[0], op="in", right=items[1])

    def matches_expr(self, items):
        return BinaryExpr(left=items[0], op="matches", right=items[1])

    def bool_call(self, items):
        return items[0]

    def bool_ref(self, items):
        return NameExpr(name=items[0])

    def literal(self, items):
        return items[0]