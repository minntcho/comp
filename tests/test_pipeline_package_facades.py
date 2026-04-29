from calculation_pass import CalculationPass as LegacyCalculationPass, CalculationPassConfig as LegacyCalculationPassConfig
from emit_pass import EmitPass as LegacyEmitPass, EmitPassConfig as LegacyEmitPassConfig
from governance_pass import GovernancePass as LegacyGovernancePass, GovernancePassConfig as LegacyGovernancePassConfig
from inference_pass import InferencePass as LegacyInferencePass, InferencePassConfig as LegacyInferencePassConfig
from lex_pass import LexPass as LegacyLexPass, LexPassConfig as LegacyLexPassConfig
from parse_pass import ParsePass as LegacyParsePass
from repair_pass import CandidateScore as LegacyCandidateScore, RepairPass as LegacyRepairPass, RepairPassConfig as LegacyRepairPassConfig
from scope_resolution_pass import ScopeResolutionPass as LegacyScopeResolutionPass
from semantic_pass import SemanticPass as LegacySemanticPass, SemanticPassConfig as LegacySemanticPassConfig

from comp.pipeline import (
    CalculationPass,
    EmitPass,
    GovernancePass,
    InferencePass,
    LexPass,
    ParsePass,
    RepairPass,
    ScopeResolutionPass,
    SemanticPass,
    SemanticPassConfig,
)
from comp.pipeline.calculation import CalculationPass as PackageCalculationPass, CalculationPassConfig as PackageCalculationPassConfig
from comp.pipeline.emit import EmitPass as PackageEmitPass, EmitPassConfig as PackageEmitPassConfig
from comp.pipeline.governance import GovernancePass as PackageGovernancePass, GovernancePassConfig as PackageGovernancePassConfig
from comp.pipeline.infer import InferencePass as PackageInferencePass, InferencePassConfig as PackageInferencePassConfig
from comp.pipeline.lex import LexPass as PackageLexPass, LexPassConfig as PackageLexPassConfig
from comp.pipeline.parsing import ParsePass as PackageParsePass
from comp.pipeline.repair import CandidateScore as PackageCandidateScore, RepairPass as PackageRepairPass, RepairPassConfig as PackageRepairPassConfig
from comp.pipeline.scope import ScopeResolutionPass as PackageScopeResolutionPass
from comp.pipeline.semantic import SemanticPass as PackageSemanticPass, SemanticPassConfig as PackageSemanticPassConfig


def test_pipeline_package_exports_match_legacy_objects():
    assert LexPass is LegacyLexPass
    assert ParsePass is LegacyParsePass
    assert ScopeResolutionPass is LegacyScopeResolutionPass
    assert InferencePass is LegacyInferencePass
    assert SemanticPass is LegacySemanticPass
    assert SemanticPassConfig is LegacySemanticPassConfig
    assert RepairPass is LegacyRepairPass
    assert EmitPass is LegacyEmitPass
    assert GovernancePass is LegacyGovernancePass
    assert CalculationPass is LegacyCalculationPass


def test_pipeline_module_facades_match_legacy_objects():
    assert PackageLexPass is LegacyLexPass
    assert PackageLexPassConfig is LegacyLexPassConfig
    assert PackageParsePass is LegacyParsePass
    assert PackageScopeResolutionPass is LegacyScopeResolutionPass
    assert PackageInferencePass is LegacyInferencePass
    assert PackageInferencePassConfig is LegacyInferencePassConfig
    assert PackageSemanticPass is LegacySemanticPass
    assert PackageSemanticPassConfig is LegacySemanticPassConfig
    assert PackageRepairPass is LegacyRepairPass
    assert PackageRepairPassConfig is LegacyRepairPassConfig
    assert PackageCandidateScore is LegacyCandidateScore
    assert PackageEmitPass is LegacyEmitPass
    assert PackageEmitPassConfig is LegacyEmitPassConfig
    assert PackageGovernancePass is LegacyGovernancePass
    assert PackageGovernancePassConfig is LegacyGovernancePassConfig
    assert PackageCalculationPass is LegacyCalculationPass
    assert PackageCalculationPassConfig is LegacyCalculationPassConfig
