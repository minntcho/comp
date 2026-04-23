from lex_eval import LexEvalError as LegacyLexEvalError, LexEvaluator as LegacyLexEvaluator

from comp.eval.lex import LexEvalError as PackageLexEvalError, LexEvaluator as PackageLexEvaluator


def test_lex_eval_wrapper_matches_package_module():
    assert LegacyLexEvalError is PackageLexEvalError
    assert LegacyLexEvaluator is PackageLexEvaluator
