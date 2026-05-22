"""Deterministic compiler-tool contract surface."""

from comp.compiler_tool.calculation_flow import resolve_reference_grounded_calculation
from comp.compiler_tool.calculation_report import apply_calculation_result
from comp.compiler_tool.calculation_resolution import plan_calculation_resolution
from comp.compiler_tool.calculation_retry import retry_blocked_calculation
from comp.compiler_tool.calculations import (
    CalculatedClaim,
    CalculationFormula,
    CalculationInput,
    CalculationRequirement,
    CalculationResult,
    CalculationStep,
    CalculationTrace,
    calculation_formula_declaration_fingerprint,
    calculate_derived_claim,
)
from comp.compiler_tool.commit_flow import CommitPreparation, prepare_commit
from comp.compiler_tool.commit_package import ReviewPackage, build_commit_package
from comp.compiler_tool.governance import (
    GovernanceStatus,
    ReviewDecision,
    decide_governance,
)
from comp.compiler_tool.judgment_adapter import (
    add_commit_preparation_facts,
    add_compile_report_facts,
    commit_preparation_to_facts,
    compile_report_to_facts,
)
from comp.compiler_tool.models import (
    CheckedClaim,
    ClaimCandidate,
    EvidenceRef,
    FailedClaim,
    Hazard,
    InterpretationHypothesis,
    SemanticJudgment,
    SemanticJudgmentRequirement,
    UncheckedArea,
    UnknownClaim,
    ValidationReport,
    ValidationRequirement,
    evidence_ref_fingerprint,
)
from comp.compiler_tool.profile_runner import compile_with_profile, run_profile_rules
from comp.compiler_tool.profiles import (
    CompilerProfile,
    DomainPack,
    JudgePolicy,
    ProfileValidationError,
    RuleFamily,
    SemanticRubric,
    active_retrieval_query_policies,
    active_rule_families,
    domain_pack_declaration_fingerprint,
    profile_allowed_units,
    profile_declaration_fingerprint,
    profile_known_fields,
    profile_lock_body,
    profile_lock_envelope_body,
    rule_family_declaration_fingerprint,
    semantic_rubric_declaration_fingerprint,
    validate_compiler_profile,
)
from comp.compiler_tool.receipt_builder import (
    ReceiptBuildBlocked,
    build_public_output_receipt,
)
from comp.compiler_tool.reference_db import (
    ReferenceCatalog,
    ReferenceCatalogSnapshot,
    ReferenceLookupError,
    ReferenceRecord,
    reference_catalog_snapshot_fingerprint,
    reference_record_fingerprint,
)
from comp.compiler_tool.reference_resolution import (
    ReferenceSearchQuery,
    resolve_reference_search_requirements,
)
from comp.compiler_tool.reference_selection_report import apply_reference_selection
from comp.compiler_tool.reference_selector import (
    ReferenceSelectionCriteria,
    ReferenceSelectionResult,
    select_reference_binding,
)
from comp.compiler_tool.references import (
    CanonicalReference,
    ReferenceOption,
    RejectedReferenceOption,
)
from comp.compiler_tool.report_status import (
    recompute_report_status,
    with_recomputed_status,
)
from comp.compiler_tool.resolver_retrieval import (
    RetrievalQueryPolicy,
    RetrievalQueryRule,
    reference_query_for_requirement_from_policies,
    reference_query_for_requirement_from_policy,
    reference_query_for_requirement_from_profile_policy,
    reference_query_for_requirement_from_resolver_tasks,
    reference_query_from_resolver_task,
)
from comp.compiler_tool.resolver_tasks import (
    ResolverTask,
    resolver_task_from_requirement,
    resolver_tasks_from_report,
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
    resolve_reference_retrieval_requirements,
)
from comp.compiler_tool.semantic import apply_semantic_judgments
from comp.compiler_tool.tool import CompilerTool
from comp.judgment.receipts import (
    DependencyFingerprint,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputValueCommitment,
)

__all__ = [
    "InterpretationHypothesis",
    "ClaimCandidate",
    "EvidenceRef",
    "evidence_ref_fingerprint",
    "ValidationReport",
    "CheckedClaim",
    "FailedClaim",
    "UnknownClaim",
    "UncheckedArea",
    "ValidationRequirement",
    "SemanticJudgmentRequirement",
    "SemanticJudgment",
    "Hazard",
    "CalculationInput",
    "CalculationFormula",
    "CalculationRequirement",
    "CalculationResult",
    "CalculationStep",
    "CalculationTrace",
    "CalculatedClaim",
    "calculation_formula_declaration_fingerprint",
    "calculate_derived_claim",
    "resolve_reference_grounded_calculation",
    "apply_calculation_result",
    "plan_calculation_resolution",
    "retry_blocked_calculation",
    "CommitPreparation",
    "prepare_commit",
    "ReviewPackage",
    "build_commit_package",
    "ReviewDecision",
    "GovernanceStatus",
    "decide_governance",
    "ReferenceOption",
    "RejectedReferenceOption",
    "CanonicalReference",
    "ReceiptBuildBlocked",
    "PublicOutputReceipt",
    "PublicOutputReceiptCitations",
    "PublicOutputValueCommitment",
    "DependencyFingerprint",
    "build_public_output_receipt",
    "ReferenceLookupError",
    "ReferenceRecord",
    "ReferenceCatalog",
    "ReferenceCatalogSnapshot",
    "reference_record_fingerprint",
    "reference_catalog_snapshot_fingerprint",
    "ReferenceSearchQuery",
    "resolve_reference_search_requirements",
    "apply_reference_selection",
    "ReferenceSelectionCriteria",
    "ReferenceSelectionResult",
    "select_reference_binding",
    "recompute_report_status",
    "with_recomputed_status",
    "ResolverTask",
    "resolver_task_from_requirement",
    "resolver_tasks_from_report",
    "RetrievalQueryPolicy",
    "RetrievalQueryRule",
    "reference_query_for_requirement_from_policies",
    "reference_query_for_requirement_from_profile_policy",
    "reference_query_for_requirement_from_policy",
    "reference_query_for_requirement_from_resolver_tasks",
    "reference_query_from_resolver_task",
    "RETRIEVAL_LENSES",
    "RetrievalLens",
    "ReferenceQuery",
    "ReferenceIndexEntry",
    "ReferenceResolver",
    "EmbeddingResolverStub",
    "ReferenceRetrievalQuery",
    "resolve_reference_retrieval_requirements",
    "RuleFamily",
    "SemanticRubric",
    "JudgePolicy",
    "DomainPack",
    "CompilerProfile",
    "ProfileValidationError",
    "validate_compiler_profile",
    "active_rule_families",
    "active_retrieval_query_policies",
    "profile_known_fields",
    "profile_allowed_units",
    "profile_declaration_fingerprint",
    "profile_lock_body",
    "profile_lock_envelope_body",
    "domain_pack_declaration_fingerprint",
    "rule_family_declaration_fingerprint",
    "semantic_rubric_declaration_fingerprint",
    "compile_with_profile",
    "run_profile_rules",
    "CompilerTool",
    "apply_semantic_judgments",
    "compile_report_to_facts",
    "add_compile_report_facts",
    "commit_preparation_to_facts",
    "add_commit_preparation_facts",
]
