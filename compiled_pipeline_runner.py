from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from lark import Lark

from artifacts import CompileArtifacts
from ast_builder import ASTBuilder
from binder import Binder
from calculation_pass import CalculationPass
from compiled_expr_eval import CompiledExprEvaluator
from compiled_spec import CompiledProgramSpec
from emit_pass import EmitPass
from governance_pass import GovernancePass
from inference_pass import InferencePass
from lex_pass import LexPass
from lowering import Lowerer
from parse_pass import ParsePass
from pipeline_runner import ESGPipelineRunner, PipelineRunResult
from repair_pass import RepairPass
from scope_resolution_pass import ScopeResolutionPass
from semantic_pass import SemanticPass


def load_compiled_program_spec_from_dsl(
    *,
    grammar_path: str | Path,
    dsl_path: str | Path | None = None,
    dsl_text: str | None = None,
) -> CompiledProgramSpec:
    if dsl_text is None and dsl_path is None:
        raise ValueError("one of dsl_text or dsl_path must be provided")
    grammar = Path(grammar_path).read_text(encoding="utf-8")
    source = dsl_text if dsl_text is not None else Path(dsl_path).read_text(encoding="utf-8")
    parser = Lark(grammar, parser="lalr", lexer="contextual", start="start")
    tree = parser.parse(source)
    return Binder().bind(Lowerer().lower(ASTBuilder().transform(tree)))


def _materialize_runtime_spec(compiled_spec: CompiledProgramSpec):
    spec = deepcopy(compiled_spec.syntax)
    for dst, src in zip(spec.constraints, compiled_spec.compiled_constraints): dst.condition = src.condition_ir
    for dst, src in zip(spec.diagnostics, compiled_spec.compiled_diagnostics): dst.condition = src.condition_ir
    for dst, src in zip(spec.infer_rules, compiled_spec.compiled_infer_rules):
        dst.value_expr = src.value_ir; dst.condition = src.condition_ir
    for name, src in compiled_spec.compiled_resolvers.items():
        if name not in spec.resolvers: continue
        dst = spec.resolvers[name]
        dst.assigns = dict(src.assigns_ir); dst.candidate_pool_assigns = dict(src.candidate_pool_assigns_ir)
        dst.commit_condition = src.commit_condition_ir; dst.review_condition = src.review_condition_ir
    for name, src in compiled_spec.compiled_governances.items():
        if name not in spec.governances: continue
        dst = spec.governances[name]
        dst.emit_condition = src.emit_condition_ir
        dst.merge_conditions = list(src.merge_conditions_ir)
        dst.forbid_merge_conditions = list(src.forbid_merge_conditions_ir)
    return spec


def build_compiled_rule_passes():
    ev = CompiledExprEvaluator()
    return [LexPass(), ParsePass(evaluator=ev), ScopeResolutionPass(), InferencePass(evaluator=ev), SemanticPass(evaluator=ev), RepairPass(evaluator=ev), EmitPass(), GovernancePass(evaluator=ev), CalculationPass()]


class CompiledESGPipelineRunner(ESGPipelineRunner):
    def __init__(self, *, grammar_path: str | Path = "esgdl.lark", passes=None, fragmentizer=None) -> None:
        super().__init__(grammar_path=grammar_path, passes=passes or build_compiled_rule_passes(), fragmentizer=fragmentizer)

    def load_spec(self, *, dsl_path: str | Path | None = None, dsl_text: str | None = None) -> CompiledProgramSpec:
        return load_compiled_program_spec_from_dsl(grammar_path=self.grammar_path, dsl_path=dsl_path, dsl_text=dsl_text)

    def run(self, *, spec=None, dsl_path: str | Path | None = None, dsl_text: str | None = None, fragments=None, documents=None, resources=None) -> PipelineRunResult:
        compiled_spec = self.load_spec(dsl_path=dsl_path, dsl_text=dsl_text) if spec is None else (spec if isinstance(spec, CompiledProgramSpec) else Binder().bind(spec))
        env = self.build_env(spec=compiled_spec.syntax, resources=resources)
        prepared_fragments = self.prepare_fragments(fragments=fragments, documents=documents)
        runtime_spec = _materialize_runtime_spec(compiled_spec)
        artifacts = CompileArtifacts(fragments=prepared_fragments)
        for p in self.passes:
            artifacts = p.run(runtime_spec, artifacts, env)
        return PipelineRunResult(spec=compiled_spec, env=env, artifacts=artifacts)
