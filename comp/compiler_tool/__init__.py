"""Deterministic compiler-tool contract surface."""

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
    "CompilerTool",
    "apply_semantic_judgments",
    "compile_report_to_facts",
    "add_compile_report_facts",
]
