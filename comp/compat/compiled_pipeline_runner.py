import importlib

_legacy = importlib.import_module("compiled_pipeline_runner")

CompiledESGPipelineRunner = getattr(_legacy, "CompiledESGPipelineRunner")

__all__ = ["CompiledESGPipelineRunner"]
