import importlib

_legacy = importlib.import_module("pipeline_runner")

ESGPipelineRunner = getattr(_legacy, "ESGPipelineRunner")
PipelineResources = getattr(_legacy, "PipelineResources")
PipelineRunResult = getattr(_legacy, "PipelineRunResult")
compile_program_spec = getattr(_legacy, "compile_program_spec")
load_compiled_program_spec_from_dsl = getattr(_legacy, "load_compiled_program_spec_from_dsl")
load_program_spec_from_dsl = getattr(_legacy, "load_program_spec_from_dsl")

__all__ = [
    "ESGPipelineRunner",
    "PipelineResources",
    "PipelineRunResult",
    "compile_program_spec",
    "load_program_spec_from_dsl",
    "load_compiled_program_spec_from_dsl",
]
