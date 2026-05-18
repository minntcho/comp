# lowering.py
from __future__ import annotations

from dataclasses import replace
from typing import Any

from ast_nodes import (
    Program,
    Expr,
    NameExpr,
    LiteralExpr,
    FunctionCallExpr,
    SetExpr,
    ColumnRefExpr,
    ContextRefExpr,
    RowLabelRefExpr,
    AlternationExpr,
    UnaryExpr,
    BinaryExpr,
    ModuleDecl,
    ImportDecl,
    DimensionDecl,
    UnitDecl,
    ActivityDecl,
    ScopeDecl,
    ContextDecl,
    PrecedenceStmt,
    RefineStmt,
    TtlStmt,
    SupportsStmt,
    FrameDecl,
    TokenDecl,
    FallbackTokenDecl,
    ParserDecl,
    BuildStmt,
    BindStmt,
    ParserInheritStmt,
    TagStmt,
    InheritRule,
    InferRule,
    RequireRule,
    ForbidRule,
    DiagnosticRule,
    ResolverDecl,
    AssignStmt,
    CandidatePoolBlock,
    CommitStmt,
    ReviewStmt,
    RejectStmt,
    GovernanceDecl,
    EmitStmt,
    MergeStmt,
    ForbidMergeStmt,
)
from spec_nodes import (
    ProgramSpec,
    DimensionSpec,
    NormalizeSpec,
    UnitSpec,
    ActivitySpec,
    ContextPolicy,
    FieldSpec,
    FrameSpec,
    TokenSpec,
    ParserSpec,
    InheritSpec,
    InferSpec,
    ConstraintSpec,
    DiagnosticSpec,
    ResolverPolicy,
    GovernancePolicy,
)


class LoweringError(ValueError):
    pass


class Lowerer:
    """
    Program(AST) -> ProgramSpec(runtime-friendly spec)

    원칙:
    - expression tree는 최대한 보존한다
    - duplicate / cross-reference / shape validation을 여기서 처리한다
    - resolver/governance는 '정책 데이터'로만 내린다
    """

    def lower(self, program: Program) -> ProgramSpec:
        if not isinstance(program, Program):
            raise TypeError("lower() expects Program AST")

        spec = ProgramSpec(module_name="main")

        seen_module = False
        seen_scope = False

        for stmt in program.statements:
            if isinstance(stmt, ModuleDecl):
                if seen_module:
                    raise LoweringError("module declaration may appear only once")
                spec.module_name = stmt.name
                seen_module = True

            elif isinstance(stmt, ImportDecl):
                spec.imports.append(stmt.name)

            elif isinstance(stmt, DimensionDecl):
                self._add_unique(
                    spec.dimensions,
                    stmt.name,
                    DimensionSpec(name=stmt.name),
                    kind="dimension",
                )

            elif isinstance(stmt, UnitDecl):
                self._lower_unit_decl(spec, stmt)

            elif isinstance(stmt, ActivityDecl):
                self._add_unique(
                    spec.activities,
                    stmt.name,
                    ActivitySpec(
                        name=stmt.name,
                        dimension=stmt.dimension,
                        scope_category=stmt.scope_category,
                    ),
                    kind="activity",
                )

            elif isinstance(stmt, ScopeDecl):
                if seen_scope:
                    raise LoweringError("scope declaration may appear only once")
                spec.scope_chain = list(stmt.chain)
                seen_scope = True

            elif isinstance(stmt, ContextDecl):
                self._lower_context_decl(spec, stmt)

            elif isinstance(stmt, FrameDecl):
                self._lower_frame_decl(spec, stmt)

            elif isinstance(stmt, TokenDecl):
                self._lower_token_decl(spec, stmt, is_fallback=False)

            elif isinstance(stmt, FallbackTokenDecl):
                self._lower_token_decl(spec, stmt, is_fallback=True)

            elif isinstance(stmt, ParserDecl):
                self._lower_parser_decl(spec, stmt)

            elif isinstance(stmt, InheritRule):
                spec.inherit_rules.append(
                    InheritSpec(
                        role_name=stmt.role_name,
                        source_expr=self._expr(stmt.source_expr),
                        condition=self._expr(stmt.condition),
                    )
                )

            elif isinstance(stmt, InferRule):
                spec.infer_rules.append(
                    InferSpec(
                        target_name=stmt.target_name,
                        op=stmt.op,
                        value_expr=self._expr(stmt.value_expr),
                        condition=self._expr(stmt.condition),
                        weight=stmt.weight,
                    )
                )

            elif isinstance(stmt, RequireRule):
                spec.constraints.append(
                    ConstraintSpec(
                        kind="require",
                        condition=self._expr(stmt.condition),
                    )
                )

            elif isinstance(stmt, ForbidRule):
                spec.constraints.append(
                    ConstraintSpec(
                        kind="forbid",
                        condition=self._expr(stmt.condition),
                        frame_name=stmt.frame_name,
                    )
                )

            elif isinstance(stmt, DiagnosticRule):
                spec.diagnostics.append(
                    DiagnosticSpec(
                        level=stmt.level,
                        code=stmt.code,
                        condition=self._expr(stmt.condition),
                    )
                )

            elif isinstance(stmt, ResolverDecl):
                self._lower_resolver_decl(spec, stmt)

            elif isinstance(stmt, GovernanceDecl):
                self._lower_governance_decl(spec, stmt)

            else:
                raise LoweringError(f"unsupported top-level AST node: {type(stmt).__name__}")

        self._validate_spec(spec)
        return spec

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _add_unique(self, target: dict[str, Any], key: str, value: Any, *, kind: str) -> None:
        if key in target:
            raise LoweringError(f"duplicate {kind}: {key}")
        target[key] = value

    def _get_or_create_token(self, spec: ProgramSpec, name: str) -> TokenSpec:
        tok = spec.tokens.get(name)
        if tok is None:
            tok = TokenSpec(name=name)
            spec.tokens[name] = tok
        return tok

    # ------------------------------------------------------------------
    # Expression normalization
    # ------------------------------------------------------------------

    def _expr(self, value: Any) -> Expr:
        """
        ASTBuilder 단계에서 bare string이 qname일 수 있으므로
        lowering 단계에서 NameExpr로 정규화한다.
        """
        if isinstance(value, Expr):
            return self._normalize_expr_tree(value)

        if isinstance(value, str):
            return NameExpr(name=value)

        if isinstance(value, (int, float, bool)):
            return LiteralExpr(value=value)

        raise LoweringError(f"cannot normalize value into Expr: {value!r}")

    def _normalize_expr_tree(self, expr: Expr) -> Expr:
        if isinstance(expr, NameExpr):
            return expr

        if isinstance(expr, LiteralExpr):
            return expr

        if isinstance(expr, FunctionCallExpr):
            return FunctionCallExpr(
                name=expr.name,
                args=[self._expr(a) for a in expr.args],
            )

        if isinstance(expr, SetExpr):
            return SetExpr(items=[self._expr(i) for i in expr.items])

        if isinstance(expr, ColumnRefExpr):
            return expr

        if isinstance(expr, ContextRefExpr):
            return expr

        if isinstance(expr, RowLabelRefExpr):
            return expr

        if isinstance(expr, AlternationExpr):
            return AlternationExpr(options=[self._expr(o) for o in expr.options])

        if isinstance(expr, UnaryExpr):
            return UnaryExpr(op=expr.op, operand=self._expr(expr.operand))

        if isinstance(expr, BinaryExpr):
            return BinaryExpr(
                left=self._expr(expr.left),
                op=expr.op,
                right=self._expr(expr.right),
            )

        raise LoweringError(f"unsupported Expr node: {type(expr).__name__}")

    # ------------------------------------------------------------------
    # Lower individual declarations
    # ------------------------------------------------------------------

    def _lower_unit_decl(self, spec: ProgramSpec, stmt: UnitDecl) -> None:
        normalize = None
        if stmt.normalize is not None:
            normalize = NormalizeSpec(
                target_unit=stmt.normalize.target_unit,
                op=stmt.normalize.op,
                factor=float(stmt.normalize.factor),
            )

        self._add_unique(
            spec.units,
            stmt.name,
            UnitSpec(
                name=stmt.name,
                dimension=stmt.dimension,
                normalize=normalize,
            ),
            kind="unit",
        )

    def _lower_context_decl(self, spec: ProgramSpec, stmt: ContextDecl) -> None:
        if stmt.role_name in spec.contexts:
            raise LoweringError(f"duplicate context block: {stmt.role_name}")

        policy = ContextPolicy(role_name=stmt.role_name)

        seen_precedence = False
        seen_ttl = False

        for s in stmt.statements:
            if isinstance(s, PrecedenceStmt):
                if seen_precedence:
                    raise LoweringError(
                        f"context {stmt.role_name}: precedence may appear only once"
                    )
                policy.precedence_chain = list(s.chain)
                seen_precedence = True

            elif isinstance(s, RefineStmt):
                policy.refine_pairs.append((s.specific, s.broad))

            elif isinstance(s, TtlStmt):
                if seen_ttl:
                    raise LoweringError(
                        f"context {stmt.role_name}: ttl may appear only once"
                    )
                policy.ttl_levels = list(s.values)
                seen_ttl = True

            elif isinstance(s, SupportsStmt):
                policy.supports.extend(s.values)

            else:
                raise LoweringError(
                    f"context {stmt.role_name}: unsupported stmt {type(s).__name__}"
                )

        spec.contexts[stmt.role_name] = policy

    def _lower_frame_decl(self, spec: ProgramSpec, stmt: FrameDecl) -> None:
        if stmt.name in spec.frames:
            raise LoweringError(f"duplicate frame: {stmt.name}")

        seen_fields: set[str] = set()
        fields: list[FieldSpec] = []

        for f in stmt.fields:
            if f.name in seen_fields:
                raise LoweringError(f"frame {stmt.name}: duplicate field {f.name}")
            seen_fields.add(f.name)

            fields.append(
                FieldSpec(
                    name=f.name,
                    type_name=f.type_ref.name,
                    generic=f.type_ref.generic,
                    optional=f.optional,
                )
            )

        spec.frames[stmt.name] = FrameSpec(name=stmt.name, fields=fields)

    def _lower_token_decl(
        self,
        spec: ProgramSpec,
        stmt: TokenDecl | FallbackTokenDecl,
        *,
        is_fallback: bool,
    ) -> None:
        tok = self._get_or_create_token(spec, stmt.name)
        expr = self._expr(stmt.expr)

        if is_fallback:
            if tok.fallback_expr is not None:
                raise LoweringError(f"duplicate fallback token rule: {stmt.name}")
            tok.fallback_expr = expr
        else:
            if tok.primary_expr is not None:
                raise LoweringError(f"duplicate token rule: {stmt.name}")
            tok.primary_expr = expr

    def _lower_parser_decl(self, spec: ProgramSpec, stmt: ParserDecl) -> None:
        if stmt.name in spec.parsers:
            raise LoweringError(f"duplicate parser: {stmt.name}")

        build_frame = None
        lowered_actions = []

        for action in stmt.actions:
            if isinstance(action, BuildStmt):
                if build_frame is not None:
                    raise LoweringError(
                        f"parser {stmt.name}: build may appear only once"
                    )
                build_frame = action.frame_name
                lowered_actions.append(action)

            elif isinstance(action, BindStmt):
                lowered_actions.append(
                    BindStmt(
                        role_name=action.role_name,
                        source_expr=self._expr(action.source_expr),
                        optional=action.optional,
                    )
                )

            elif isinstance(action, ParserInheritStmt):
                lowered_actions.append(
                    ParserInheritStmt(
                        role_name=action.role_name,
                        source_expr=self._expr(action.source_expr),
                        condition=self._expr(action.condition) if action.condition is not None else None,
                    )
                )

            elif isinstance(action, TagStmt):
                lowered_actions.append(
                    TagStmt(
                        role_name=action.role_name,
                        source_expr=self._expr(action.source_expr),
                    )
                )

            else:
                raise LoweringError(
                    f"parser {stmt.name}: unsupported action {type(action).__name__}"
                )

        if build_frame is None:
            raise LoweringError(f"parser {stmt.name}: missing build statement")

        spec.parsers[stmt.name] = ParserSpec(
            name=stmt.name,
            source_selectors=list(stmt.source_selectors),
            build_frame=build_frame,
            actions=lowered_actions,
        )

    def _lower_resolver_decl(self, spec: ProgramSpec, stmt: ResolverDecl) -> None:
        if stmt.frame_name in spec.resolvers:
            raise LoweringError(f"duplicate resolver for frame: {stmt.frame_name}")

        policy = ResolverPolicy(frame_name=stmt.frame_name)

        for s in stmt.statements:
            if isinstance(s, AssignStmt):
                if s.name in policy.assigns:
                    raise LoweringError(
                        f"resolver {stmt.frame_name}: duplicate assign {s.name}"
                    )
                policy.assigns[s.name] = self._expr(s.value)

            elif isinstance(s, CandidatePoolBlock):
                for a in s.assigns:
                    if a.name in policy.candidate_pool_assigns:
                        raise LoweringError(
                            f"resolver {stmt.frame_name}: duplicate candidate_pool assign {a.name}"
                        )
                    policy.candidate_pool_assigns[a.name] = self._expr(a.value)

            elif isinstance(s, CommitStmt):
                if policy.commit_condition is not None:
                    raise LoweringError(
                        f"resolver {stmt.frame_name}: duplicate commit clause"
                    )
                policy.commit_condition = self._expr(s.condition)

            elif isinstance(s, ReviewStmt):
                if policy.review_condition is not None:
                    raise LoweringError(
                        f"resolver {stmt.frame_name}: duplicate review clause"
                    )
                policy.review_condition = self._expr(s.condition)

            elif isinstance(s, RejectStmt):
                if policy.reject_otherwise:
                    raise LoweringError(
                        f"resolver {stmt.frame_name}: duplicate reject otherwise"
                    )
                policy.reject_otherwise = True

            else:
                raise LoweringError(
                    f"resolver {stmt.frame_name}: unsupported stmt {type(s).__name__}"
                )

        spec.resolvers[stmt.frame_name] = policy

    def _lower_governance_decl(self, spec: ProgramSpec, stmt: GovernanceDecl) -> None:
        if stmt.frame_name in spec.governances:
            raise LoweringError(f"duplicate governance for frame: {stmt.frame_name}")

        policy = GovernancePolicy(frame_name=stmt.frame_name)

        for s in stmt.statements:
            if isinstance(s, EmitStmt):
                if policy.emit_condition is not None:
                    raise LoweringError(
                        f"governance {stmt.frame_name}: duplicate emit row clause"
                    )
                policy.emit_condition = self._expr(s.condition)

            elif isinstance(s, MergeStmt):
                policy.merge_conditions.append(self._expr(s.condition))

            elif isinstance(s, ForbidMergeStmt):
                policy.forbid_merge_conditions.append(self._expr(s.condition))

            else:
                raise LoweringError(
                    f"governance {stmt.frame_name}: unsupported stmt {type(s).__name__}"
                )

        spec.governances[stmt.frame_name] = policy

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_spec(self, spec: ProgramSpec) -> None:
        # Unit dimensions must exist
        for unit in spec.units.values():
            if unit.dimension not in spec.dimensions:
                raise LoweringError(
                    f"unit {unit.name}: unknown dimension {unit.dimension}"
                )
            if unit.normalize is not None and unit.normalize.target_unit not in spec.units:
                raise LoweringError(
                    f"unit {unit.name}: normalize target unit {unit.normalize.target_unit} not declared"
                )

        # Activity dimensions must exist
        for act in spec.activities.values():
            if act.dimension not in spec.dimensions:
                raise LoweringError(
                    f"activity {act.name}: unknown dimension {act.dimension}"
                )

        # Token specs must have at least one implementation
        for tok in spec.tokens.values():
            if tok.primary_expr is None and tok.fallback_expr is None:
                raise LoweringError(f"token {tok.name}: no primary/fallback expr")

        # Parser build frame must exist
        for parser in spec.parsers.values():
            if parser.build_frame not in spec.frames:
                raise LoweringError(
                    f"parser {parser.name}: unknown build frame {parser.build_frame}"
                )

        # Forbid frame references must exist
        for c in spec.constraints:
            if c.frame_name is not None and c.frame_name not in spec.frames:
                raise LoweringError(
                    f"constraint references unknown frame: {c.frame_name}"
                )

        # Resolver/governance target frames must exist
        for frame_name in spec.resolvers:
            if frame_name not in spec.frames:
                raise LoweringError(
                    f"resolver references unknown frame: {frame_name}"
                )

        for frame_name in spec.governances:
            if frame_name not in spec.frames:
                raise LoweringError(
                    f"governance references unknown frame: {frame_name}"
                )