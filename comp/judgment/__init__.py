"""Judgment-core exports for the next architecture step."""

from comp.judgment.commit import (
    DraftSnapshot,
    PublicOutput,
    PublicOutputBlocked,
    ProjectionBlocked,
    blocking_hazards_clear,
    committable,
    project_public_row,
    prov_enough,
    resolved_required_bundles,
)
from comp.judgment.core import Fact, FactTag, JudgmentState, SubjectKind, SubjectRef
from comp.judgment.engine import FixpointEngine
from comp.judgment.frontier import (
    CandidateSummary,
    dominates,
    frontier,
    needs_review,
    winner_or_none,
)
from comp.judgment.program import (
    BundleSpec,
    CommitSpec,
    CompiledJudgmentProgram,
    PublicOutputSpec,
    ProjectionSpec,
    TransferEmitter,
    TransferRule,
)
from comp.judgment.receipts import (
    CommitReceipt,
    CommitReceiptCitations,
    DependencyFingerprint,
    ProjectionValueCommitment,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    SelectionReceipt,
)

__all__ = [
    "SubjectKind",
    "FactTag",
    "SubjectRef",
    "Fact",
    "JudgmentState",
    "TransferEmitter",
    "TransferRule",
    "BundleSpec",
    "CommitSpec",
    "PublicOutputSpec",
    "ProjectionSpec",
    "CompiledJudgmentProgram",
    "FixpointEngine",
    "CandidateSummary",
    "dominates",
    "frontier",
    "winner_or_none",
    "needs_review",
    "DraftSnapshot",
    "PublicOutput",
    "PublicOutputBlocked",
    "ProjectionBlocked",
    "resolved_required_bundles",
    "blocking_hazards_clear",
    "prov_enough",
    "committable",
    "project_public_row",
    "SelectionReceipt",
    "ProjectionValueCommitment",
    "DependencyFingerprint",
    "PublicOutputReceipt",
    "PublicOutputReceiptCitations",
    "CommitReceipt",
    "CommitReceiptCitations",
]
