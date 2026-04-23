from ast_nodes import BinaryExpr as LegacyBinaryExpr, Program as LegacyProgram

from comp.dsl.ast_nodes import BinaryExpr as PackageBinaryExpr, Program as PackageProgram


def test_ast_nodes_wrapper_matches_package_module():
    assert LegacyProgram is PackageProgram
    assert LegacyBinaryExpr is PackageBinaryExpr
