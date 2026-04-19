from __future__ import annotations

from pathlib import Path

from compiled_spec import CompiledProgramSpec
from pipeline_runner import ESGPipelineRunner, load_compiled_program_spec_from_dsl


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
