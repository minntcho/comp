from compiled_pipeline_runner import CompiledESGPipelineRunner as LegacyCompiledRunner
from pipeline_runner import (
    ESGPipelineRunner as LegacyRunner,
    PipelineResources as LegacyPipelineResources,
    PipelineRunResult as LegacyPipelineRunResult,
    compile_program_spec as legacy_compile_program_spec,
    load_compiled_program_spec_from_dsl as legacy_load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl as legacy_load_program_spec_from_dsl,
)

from comp.compiled_pipeline_runner import CompiledESGPipelineRunner as PackageCompiledRunner
from comp.compat.compiled_pipeline_runner import CompiledESGPipelineRunner as CompatCompiledRunner
from comp.compat.pipeline_runner import (
    ESGPipelineRunner as CompatRunner,
    PipelineResources as CompatPipelineResources,
    PipelineRunResult as CompatPipelineRunResult,
    compile_program_spec as compat_compile_program_spec,
    load_compiled_program_spec_from_dsl as compat_load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl as compat_load_program_spec_from_dsl,
)
from comp.pipeline_runner import (
    ESGPipelineRunner as PackageRunner,
    PipelineResources as PackagePipelineResources,
    PipelineRunResult as PackagePipelineRunResult,
    compile_program_spec as package_compile_program_spec,
    load_compiled_program_spec_from_dsl as package_load_compiled_program_spec_from_dsl,
    load_program_spec_from_dsl as package_load_program_spec_from_dsl,
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


def test_top_level_runner_wrappers_match_package_exports():
    assert LegacyRunner is PackageRunner
    assert LegacyCompiledRunner is PackageCompiledRunner
    assert LegacyPipelineResources is PackagePipelineResources
    assert LegacyPipelineRunResult is PackagePipelineRunResult
    assert legacy_compile_program_spec is package_compile_program_spec
    assert legacy_load_program_spec_from_dsl is package_load_program_spec_from_dsl
    assert legacy_load_compiled_program_spec_from_dsl is package_load_compiled_program_spec_from_dsl


def test_runner_compat_facades_match_package_exports():
    assert CompatRunner is PackageRunner
    assert CompatCompiledRunner is PackageCompiledRunner
    assert CompatPipelineResources is PackagePipelineResources
    assert CompatPipelineRunResult is PackagePipelineRunResult
    assert compat_compile_program_spec is package_compile_program_spec
    assert compat_load_program_spec_from_dsl is package_load_program_spec_from_dsl
    assert compat_load_compiled_program_spec_from_dsl is package_load_compiled_program_spec_from_dsl


def test_comp_runner_exports_use_package_implementation():
    assert PipelineResources is PackagePipelineResources
    assert PipelineRunResult is PackagePipelineRunResult
    assert compile_program_spec is package_compile_program_spec
    assert load_program_spec_from_dsl is package_load_program_spec_from_dsl
    assert load_compiled_program_spec_from_dsl is package_load_compiled_program_spec_from_dsl
    assert issubclass(ESGPipelineRunner, PackageRunner)
    assert issubclass(CompiledESGPipelineRunner, PackageCompiledRunner)
