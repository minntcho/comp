from compiled_pipeline_runner import CompiledESGPipelineRunner as LegacyCompiledRunner
from pipeline_runner import (
    ESGPipelineRunner as LegacyRunner,
    PipelineResources as LegacyPipelineResources,
    PipelineRunResult as LegacyPipelineRunResult,
    compile_program_spec as legacy_compile_program_spec,
    load_compiled_program_spec_from_dsl as legacy_load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl as legacy_load_program_spec_from_dsl,
)

from comp.compat.compiled_pipeline_runner import CompiledESGPipelineRunner as CompatCompiledRunner
from comp.compat.pipeline_runner import (
    ESGPipelineRunner as CompatRunner,
    PipelineResources as CompatPipelineResources,
    PipelineRunResult as CompatPipelineRunResult,
    compile_program_spec as compat_compile_program_spec,
    load_compiled_program_spec_from_dsl as compat_load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl as compat_load_program_spec_from_dsl,
)
from comp.runner import (
    CompiledESGPipelineRunner,
    ESGPipelineRunner,
    PipelineResources,
    PipelineRunResult,
    compile_program_spec,
    load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl,
)


def test_runner_compat_facades_match_legacy_exports():
    assert CompatRunner is LegacyRunner
    assert CompatCompiledRunner is LegacyCompiledRunner
    assert CompatPipelineResources is LegacyPipelineResources
    assert CompatPipelineRunResult is LegacyPipelineRunResult
    assert compat_compile_program_spec is legacy_compile_program_spec
    assert compat_load_program_spec_from_dsl is legacy_load_program_spec_from_dsl
    assert compat_load_compiled_program_spec_from_dsl is legacy_load_compiled_program_spec_from_dsl


def test_comp_runner_exports_use_compat_facades():
    assert PipelineResources is CompatPipelineResources
    assert PipelineRunResult is CompatPipelineRunResult
    assert compile_program_spec is compat_compile_program_spec
    assert load_program_spec_from_dsl is compat_load_program_spec_from_dsl
    assert load_compiled_program_spec_from_dsl is compat_load_compiled_program_spec_from_dsl
    assert issubclass(ESGPipelineRunner, CompatRunner)
    assert issubclass(CompiledESGPipelineRunner, CompatCompiledRunner)
