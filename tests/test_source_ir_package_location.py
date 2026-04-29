from source_ir import SourceCandidate as LegacySourceCandidate, SourceExpr as LegacySourceExpr

from comp.dsl.source_ir import SourceCandidate as PackageSourceCandidate, SourceExpr as PackageSourceExpr


def test_source_ir_wrapper_matches_package_module():
    assert LegacySourceCandidate is PackageSourceCandidate
    assert LegacySourceExpr is PackageSourceExpr
