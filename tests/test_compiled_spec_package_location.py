from compiled_spec import CompiledProgramSpec as LegacyCompiledProgramSpec
from compiled_spec import CompiledTokenSpec as LegacyCompiledTokenSpec

from comp.compat.compiled_spec import CompiledProgramSpec as CompatCompiledProgramSpec
from comp.compat.compiled_spec import CompiledTokenSpec as CompatCompiledTokenSpec
from comp.dsl.compiled_spec import CompiledProgramSpec as PackageCompiledProgramSpec
from comp.dsl.compiled_spec import CompiledTokenSpec as PackageCompiledTokenSpec


def test_compiled_spec_wrappers_match_package_module():
    assert LegacyCompiledProgramSpec is PackageCompiledProgramSpec
    assert LegacyCompiledTokenSpec is PackageCompiledTokenSpec
    assert CompatCompiledProgramSpec is PackageCompiledProgramSpec
    assert CompatCompiledTokenSpec is PackageCompiledTokenSpec
