"""Stable compiler-tool onboarding surface."""

from comp.compiler_tool.commit_flow import prepare_commit
from comp.compiler_tool.judgment_adapter import compile_report_to_facts
from comp.compiler_tool.models import (
    ClaimCandidate,
    EvidenceRef,
    InterpretationHypothesis,
    ValidationReport,
)
from comp.compiler_tool.receipt_builder import build_public_output_receipt
from comp.compiler_tool.resolver_tasks import resolver_tasks_from_report
from comp.compiler_tool.tool import CompilerTool

__all__ = [
    "InterpretationHypothesis",
    "ClaimCandidate",
    "EvidenceRef",
    "CompilerTool",
    "ValidationReport",
    "resolver_tasks_from_report",
    "prepare_commit",
    "build_public_output_receipt",
    "compile_report_to_facts",
]
