"""Deterministic compiler-tool contract surface."""

from comp.compiler_tool.calculations import (
    CalculationFormula,
    CalculationInput,
    CalculationRequirement,
    CalculationResult,
    CalculationStep,
    CalculationTrace,
    DerivedClaim,
    calculate_derived_claim,
)
from comp.compiler_tool.calculation_report import apply_calculation_result
from comp.compiler_tool.models import (
    CheckedClaim,
    ClaimHypothesis,
    CompileReport,
    EvidenceWitness,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    ProofObligation,
    SemanticJudgment,
    SemanticJudgmentRequirement,
    UncheckedArea,
    UnknownClaim,
)
from comp.compiler_tool.profiles import (
    CompilerProfile,
    DomainPack,
    JudgePolicy,
    ProfileValidationError,
    RuleFamily,
    SemanticRubric,
    active_rule_families,
    validate_compiler_profile,
)
from comp.compiler_tool.profile_runner import compile_with_profile
from comp.compiler_tool.reference_db import (
    ReferenceCatalog,
    ReferenceLookupError,
    ReferenceRecord,
)
from comp.compiler_tool.reference_selector import (
    ReferenceSelectionCriteria,
    ReferenceSelectionResult,
    select_reference_binding,
)
from comp.compiler_tool.references import (
    ReferenceBinding,
    ReferenceCandidate,
    RejectedReferenceCandidate,
)
from comp.compiler_tool.semantic import apply_semantic_judgments
from comp.compiler_tool.tool import CompilerTool
from comp.compiler_tool.judgment_adapter import (
    add_compile_report_facts,
    compile_report_to_facts,
)

__all__ = [
    "InterpretationHypothesis",
    "ClaimHypothesis",
    "EvidenceWitness",
    "CompileReport",
    "CheckedClaim",
    "FailedClaim",
    "UnknownClaim",
    "UncheckedArea",
    "ProofObligation",
    "SemanticJudgmentRequirement",
    "SemanticJudgment",
    "Hazard",
    "CalculationInput",
    "CalculationFormula",
    "CalculationRequirement",
    "CalculationResult",
    "CalculationStep",
    "CalculationTrace",
    "DerivedClaim",
    "calculate_derived_claim",
    "apply_calculation_result",
    "ReferenceCandidate",
    "RejectedReferenceCandidate",
    "ReferenceBinding",
    "ReferenceLookupError",
    "ReferenceRecord",
    "ReferenceCatalog",
    "ReferenceSelectionCriteria",
    "ReferenceSelectionResult",
    "select_reference_binding",
    "RuleFamily",
    "SemanticRubric",
    "JudgePolicy",
    "DomainPack",
    "CompilerProfile",
    "ProfileValidationError",
    "validate_compiler_profile",
    "active_rule_families",
    "compile_with_profile",
    "CompilerTool",
    "apply_semantic_judgments",
    "compile_report_to_facts",
    "add_compile_report_facts",
]
