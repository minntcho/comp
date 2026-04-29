from spec_nodes import FieldSpec as LegacyFieldSpec, ProgramSpec as LegacyProgramSpec

from comp.dsl.spec_nodes import FieldSpec as PackageFieldSpec, ProgramSpec as PackageProgramSpec


def test_spec_nodes_wrapper_matches_package_module():
    assert LegacyProgramSpec is PackageProgramSpec
    assert LegacyFieldSpec is PackageFieldSpec
