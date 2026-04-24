"""Top-level package entrypoint for the experimental comp package.

Keep the package import light: runner-facing symbols are resolved lazily so
``import comp`` does not eagerly import the legacy runner bridge.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_RUNNER_EXPORTS = {
    "ESGPipelineRunner",
    "CompiledESGPipelineRunner",
    "PipelineResources",
    "PipelineRunResult",
    "compile_program_spec",
    "load_program_spec_from_dsl",
    "load_compiled_program_spec_from_dsl",
}

__all__ = sorted(_RUNNER_EXPORTS)


def __getattr__(name: str) -> Any:
    if name in _RUNNER_EXPORTS:
        value = getattr(import_module("comp.runner"), name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _RUNNER_EXPORTS)
