from source_eval import SourceEvalError as LegacySourceEvalError, SourceEvaluator as LegacySourceEvaluator

from comp.eval.source_module import SourceEvalError as PackageSourceEvalError, SourceEvaluator as PackageSourceEvaluator


def test_source_eval_wrapper_matches_package_module():
    assert LegacySourceEvalError is PackageSourceEvalError
    assert LegacySourceEvaluator is PackageSourceEvaluator
