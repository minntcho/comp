from lex_ir import LexBuiltinCall as LegacyLexBuiltinCall, LexExpr as LegacyLexExpr

from comp.dsl.lex_ir import LexBuiltinCall as PackageLexBuiltinCall, LexExpr as PackageLexExpr


def test_lex_ir_wrapper_matches_package_module():
    assert LegacyLexExpr is PackageLexExpr
    assert LegacyLexBuiltinCall is PackageLexBuiltinCall
