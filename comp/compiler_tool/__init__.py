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
from comp.compiler_tool.calculation_flow import resolve_reference_grounded_calculation
from comp.compiler_tool.calculation_report import apply_calculation_result
from comp.compiler_tool.calculation_resolution import plan_calculation_resolution
from comp.compiler_tool.calculation_retry import retry_blocked_calculation
from comp.compiler_tool.commit_flow import CommitPreparation, prepare_commit
from comp.compiler_tool.commit_package import CommitPackage, build_commit_package
from comp.compiler_tool.governance import (
    GovernanceDecision,
    GovernanceStatus,
    decide_governance,
)
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
from comp.compiler_tool.reference_resolution import (
    ReferenceSearchQuery,
    resolve_reference_search_obligations,
)
from comp.compiler_tool.reference_selection_report import apply_reference_selection
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
from comp.compiler_tool.receipt_builder import (
    ReceiptBuildBlocked,
    build_commit_receipt,
)
from comp.judgment.receipts import CommitReceiptCitations, ProjectionValueCommitment
from comp.compiler_tool.report_status import (
    recompute_report_status,
    with_recomputed_status,
)
from comp.compiler_tool.resolver_tasks import (
    ResolverTask,
    resolver_task_from_obligation,
    resolver_tasks_from_report,
)
from comp.compiler_tool.resolver_retrieval import (
    reference_query_for_obligation_from_resolver_tasks,
    reference_query_from_resolver_task,
)
from comp.compiler_tool.retrieval import (
    RETRIEVAL_LENSES,
    EmbeddingResolverStub,
    ReferenceIndexEntry,
    ReferenceQuery,
    ReferenceResolver,
    RetrievalLens,
)
from comp.compiler_tool.retrieval_resolution import (
    ReferenceRetrievalQuery,
    resolve_reference_retrieval_obligations,
)
from comp.compiler_tool.semantic import apply_semantic_judgments
from comp.compiler_tool.tool import CompilerTool
from comp.compiler_tool.judgment_adapter import (
    add_commit_preparation_facts,
    add_compile_report_facts,
    commit_preparation_to_facts,
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
    "resolve_reference_grounded_calculation",
    "apply_calculation_result",
    "plan_calculation_resolution",
    "retry_blocked_calculation",
    "CommitPreparation",
    "prepare_commit",
    "CommitPackage",
    "build_commit_package",
    "GovernanceDecision",
    "GovernanceStatus",
    "decide_governance",
    "ReferenceCandidate",
    "RejectedReferenceCandidate",
    "ReferenceBinding",
    "ReceiptBuildBlocked",
    "CommitReceiptCitations",
    "ProjectionValueCommitment",
    "build_commit_receipt",
    "ReferenceLookupError",
    "ReferenceRecord",
    "ReferenceCatalog",
    "ReferenceSearchQuery",
    "resolve_reference_search_obligations",
    "apply_reference_selection",
    "ReferenceSelectionCriteria",
    "ReferenceSelectionResult",
    "select_reference_binding",
    "recompute_report_status",
    "with_recomputed_status",
    "ResolverTask",
    "resolver_task_from_obligation",
    "resolver_tasks_from_report",
    "reference_query_for_obligation_from_resolver_tasks",
    "reference_query_from_resolver_task",
    "RETRIEVAL_LENSES",
    "RetrievalLens",
    "ReferenceQuery",
    "ReferenceIndexEntry",
    "ReferenceResolver",
    "EmbeddingResolverStub",
    "ReferenceRetrievalQuery",
    "resolve_reference_retrieval_obligations",
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
    "commit_preparation_to_facts",
    "add_commit_preparation_facts",
]
