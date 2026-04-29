from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional, Protocol, Sequence

from binder import Binder
from comp.artifacts import CompileArtifacts
from comp.builtins.esg import register_default_builtins
from comp.dsl.compiled_spec import CompiledProgramSpec
from comp.dsl.spec_nodes import ProgramSpec
from comp.pipeline.calculation import CalculationPass
from comp.pipeline.emit import EmitPass
from comp.pipeline.governance import GovernancePass
from comp.pipeline.infer import InferencePass
from comp.pipeline.lex import LexPass
from comp.pipeline.parsing import ParsePass
from comp.pipeline.repair import RepairPass
from comp.pipeline.scope import ScopeResolutionPass
from comp.pipeline.semantic import SemanticPass, SemanticPassConfig
from comp.runtime_env import RuntimeEnv, SiteRecord, build_runtime_env


class Fragmentizer(Protocol):
    def __call__(self, documents: Sequence[Any]) -> list[Any]:
        ...


class CompilerPass(Protocol):
    def run(self, spec: ProgramSpec | CompiledProgramSpec, artifacts: CompileArtifacts, env: RuntimeEnv) -> CompileArtifacts:
        ...


@dataclass
class PipelineResources:
    site_records: Sequence[SiteRecord] = field(default_factory=list)
    factor_rows: Sequence[dict[str, Any]] = field(default_factory=list)
    policy_flags: dict[str, Any] = field(default_factory=dict)
    activity_aliases: dict[str, list[str]] = field(default_factory=dict)
    unit_aliases: dict[str, list[str]] = field(default_factory=dict)
    llm_fallback: Optional[Any] = None
    llm_budget: int = 0


@dataclass
class PipelineRunResult:
    spec: ProgramSpec | CompiledProgramSpec
    env: RuntimeEnv
    artifacts: CompileArtifacts

    def summary(self) -> dict[str, Any]:
        frame_status_counts: dict[str, int] = {}
        for f in self.artifacts.frames:
            frame_status_counts[f.status] = frame_status_counts.get(f.status, 0) + 1

        row_status_counts: dict[str, int] = {}
        for r in self.artifacts.rows:
            row_status_counts[r.status] = row_status_counts.get(r.status, 0) + 1

        calc_status_counts: dict[str, int] = {}
        for c in self.artifacts.calculations:
            calc_status_counts[c.calculation_status] = calc_status_counts.get(c.calculation_status, 0) + 1

        return {
            "module_name": self.spec.module_name,
            "fragments": len(self.artifacts.fragments),
            "tokens": len(self.artifacts.tokens),
            "claims": len(self.artifacts.claims),
            "frames": len(self.artifacts.frames),
            "rows": len(self.artifacts.rows),
            "calculations": len(self.artifacts.calculations),
            "frame_status_counts": frame_status_counts,
            "row_status_counts": row_status_counts,
            "calculation_status_counts": calc_status_counts,
            "merge_decisions": len(self.artifacts.merge_log),
            "events": len(self.artifacts.event_log),
            "diagnostics": len(self.artifacts.diagnostics),
            "llm_budget_remaining": self.env.llm_budget_remaining,
        }


def load_program_spec_from_dsl(*, grammar_path: str | Path, dsl_path: str | Path | None = None, dsl_text: str | None = None) -> ProgramSpec:
    if dsl_text is None and dsl_path is None:
        raise ValueError("one of dsl_text or dsl_path must be provided")
    grammar = Path(grammar_path).read_text(encoding="utf-8")
    source = dsl_text if dsl_text is not None else Path(dsl_path).read_text(encoding="utf-8")
    from lark import Lark
    from ast_builder import ASTBuilder
    from lowering import Lowerer

    parser = Lark(grammar, parser="lalr", lexer="contextual", start="start")
    tree = parser.parse(source)
    return Lowerer().lower(ASTBuilder().transform(tree))


def compile_program_spec(program_spec: ProgramSpec) -> CompiledProgramSpec:
    return Binder().bind(program_spec)


def load_compiled_program_spec_from_dsl(*, grammar_path: str | Path, dsl_path: str | Path | None = None, dsl_text: str | None = None) -> CompiledProgramSpec:
    return compile_program_spec(load_program_spec_from_dsl(grammar_path=grammar_path, dsl_path=dsl_path, dsl_text=dsl_text))


def build_default_passes(*, include_post_repair_semantic: bool = False) -> list[CompilerPass]:
    passes: list[CompilerPass] = [
        LexPass(),
        ParsePass(),
        ScopeResolutionPass(),
        InferencePass(),
        SemanticPass(config=SemanticPassConfig(phase_label="semantic_pre")),
        RepairPass(),
    ]
    if include_post_repair_semantic:
        passes.append(SemanticPass(config=SemanticPassConfig(phase_label="semantic_post")))
    passes.extend([EmitPass(), GovernancePass(), CalculationPass()])
    return passes


class ESGPipelineRunner:
    def __init__(self, *, grammar_path: str | Path = "esgdl.lark", passes: Optional[list[CompilerPass]] = None, fragmentizer: Optional[Fragmentizer] = None) -> None:
        self.grammar_path = Path(grammar_path)
        self.fragmentizer = fragmentizer
        self.passes = passes or build_default_passes()

    def load_spec(self, *, dsl_path: str | Path | None = None, dsl_text: str | None = None) -> CompiledProgramSpec:
        return load_compiled_program_spec_from_dsl(grammar_path=self.grammar_path, dsl_path=dsl_path, dsl_text=dsl_text)

    def build_env(self, *, spec: ProgramSpec | CompiledProgramSpec, resources: Optional[PipelineResources] = None) -> RuntimeEnv:
        resources = resources or PipelineResources()
        syntax_spec = spec.syntax if isinstance(spec, CompiledProgramSpec) else spec
        env = build_runtime_env(spec=syntax_spec, site_records=list(resources.site_records), factor_rows=list(resources.factor_rows), policy_flags=dict(resources.policy_flags), activity_aliases=dict(resources.activity_aliases), unit_aliases=dict(resources.unit_aliases), llm_fallback=resources.llm_fallback, llm_budget=resources.llm_budget)
        register_default_builtins(env)
        return env

    def prepare_fragments(self, *, fragments: Optional[list[Any]] = None, documents: Optional[Sequence[Any]] = None) -> list[Any]:
        if fragments is not None:
            return fragments
        if documents is None:
            raise ValueError("one of fragments or documents must be provided")
        if self.fragmentizer is None:
            raise ValueError("documents were provided but no fragmentizer is configured. Either pass pre-built fragments or inject a fragmentizer callable.")
        return self.fragmentizer(documents)

    def run(self, *, spec: Optional[ProgramSpec | CompiledProgramSpec] = None, dsl_path: str | Path | None = None, dsl_text: str | None = None, fragments: Optional[list[Any]] = None, documents: Optional[Sequence[Any]] = None, resources: Optional[PipelineResources] = None) -> PipelineRunResult:
        if spec is None:
            spec = self.load_spec(dsl_path=dsl_path, dsl_text=dsl_text)
        elif not isinstance(spec, CompiledProgramSpec):
            spec = compile_program_spec(spec)

        env = self.build_env(spec=spec, resources=resources)
        prepared_fragments = self.prepare_fragments(fragments=fragments, documents=documents)
        artifacts = CompileArtifacts(fragments=prepared_fragments)
        for p in self.passes:
            artifacts = p.run(spec, artifacts, env)
        return PipelineRunResult(spec=spec, env=env, artifacts=artifacts)


__all__ = [
    "Fragmentizer",
    "CompilerPass",
    "PipelineResources",
    "PipelineRunResult",
    "load_program_spec_from_dsl",
    "compile_program_spec",
    "load_compiled_program_spec_from_dsl",
    "build_default_passes",
    "ESGPipelineRunner",
]
