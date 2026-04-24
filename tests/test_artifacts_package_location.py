import artifacts as legacy
import comp.artifacts as package
import comp.compat.artifacts as compat


def test_artifacts_wrappers_match_package_module():
    assert legacy.CompileArtifacts is package.CompileArtifacts
    assert legacy.TokenOccurrence is package.TokenOccurrence
    assert legacy.ClaimArtifact is package.ClaimArtifact
    assert legacy.RoleSlotArtifact is package.RoleSlotArtifact
    assert legacy.PartialFrameArtifact is package.PartialFrameArtifact
    assert legacy.CanonicalRowArtifact is package.CanonicalRowArtifact
    assert legacy.DiagnosticArtifact is package.DiagnosticArtifact
    assert legacy.GovernanceDecisionArtifact is package.GovernanceDecisionArtifact
    assert legacy.CalculationArtifact is package.CalculationArtifact
    assert legacy.warning_codes_from_diagnostics is package.warning_codes_from_diagnostics
    assert legacy.error_codes_from_diagnostics is package.error_codes_from_diagnostics

    assert compat.CompileArtifacts is package.CompileArtifacts
    assert compat.TokenOccurrence is package.TokenOccurrence
    assert compat.ClaimArtifact is package.ClaimArtifact
    assert compat.RoleSlotArtifact is package.RoleSlotArtifact
    assert compat.PartialFrameArtifact is package.PartialFrameArtifact
    assert compat.CanonicalRowArtifact is package.CanonicalRowArtifact
    assert compat.DiagnosticArtifact is package.DiagnosticArtifact
    assert compat.GovernanceDecisionArtifact is package.GovernanceDecisionArtifact
    assert compat.CalculationArtifact is package.CalculationArtifact
    assert compat.warning_codes_from_diagnostics is package.warning_codes_from_diagnostics
    assert compat.error_codes_from_diagnostics is package.error_codes_from_diagnostics
