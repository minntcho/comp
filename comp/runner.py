from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from comp.compat.compiled_pipeline_runner import CompiledESGPipelineRunner as _LegacyCompiledRunner
from comp.compat.pipeline_runner import (
    ESGPipelineRunner as _LegacyRunner,
    PipelineResources,
    PipelineRunResult,
    compile_program_spec,
    load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl,
)

_DEFAULT_GRAMMAR_PATH = Path(__file__).resolve().parent / "dsl" / "esgdl.lark"


class ESGPipelineRunner(_LegacyRunner):
    def __init__(
        self,
        *,
        grammar_path: str | Path | None = None,
        passes: Optional[list[Any]] = None,
        fragmentizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            grammar_path=grammar_path or _DEFAULT_GRAMMAR_PATH,
            passes=passes,
            fragmentizer=fragmentizer,
        )


class CompiledESGPipelineRunner(_LegacyCompiledRunner):
    def __init__(
        self,
        *,
        grammar_path: str | Path | None = None,
        passes: Optional[list[Any]] = None,
        fragmentizer: Optional[Any] = None,
    ) -> None:
        super().__init__(
            grammar_path=grammar_path or _DEFAULT_GRAMMAR_PATH,
            passes=passes,
            fragmentizer=fragmentizer,
        )


__all__ = [
    "ESGPipelineRunner",
    "CompiledESGPipelineRunner",
    "PipelineResources",
    "PipelineRunResult",
    "compile_program_spec",
    "load_program_spec_from_dsl",
    "load_compiled_program_spec_from_dsl",
]
