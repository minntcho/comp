from __future__ import annotations

from pathlib import Path

from lark import Lark

from ast_builder import ASTBuilder
from binder import Binder
from compiled_spec import CompiledProgramSpec
from lowering import Lowerer
from pipeline_runner import ESGPipelineRunner


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

    parser = Lark(
        grammar,
        parser="lalr",
        lexer="contextual",
        start="start",
    )
    tree = parser.parse(source)
    program_ast = ASTBuilder().transform(tree)
    program_spec = Lowerer().lower(program_ast)
    return Binder().bind(program_spec)


class CompiledESGPipelineRunner(ESGPipelineRunner):
    def load_spec(
        self,
        *,
        dsl_path: str | Path | None = None,
        dsl_text: str | None = None,
    ) -> CompiledProgramSpec:
        return load_compiled_program_spec_from_dsl(
            grammar_path=self.grammar_path,
            dsl_path=dsl_path,
            dsl_text=dsl_text,
        )
