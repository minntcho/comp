"""Judgment-core exports for the next architecture step."""

from comp.judgment.commit import (
    DraftSnapshot,
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
    ProjectionSpec,
    TransferEmitter,
    TransferRule,
)
from comp.judgment.receipts import CommitReceipt, SelectionReceipt

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
    "ProjectionSpec",
    "CompiledJudgmentProgram",
    "FixpointEngine",
    "CandidateSummary",
    "dominates",
    "frontier",
    "winner_or_none",
    "needs_review",
    "DraftSnapshot",
    "resolved_required_bundles",
    "blocking_hazards_clear",
    "prov_enough",
    "committable",
    "project_public_row",
    "SelectionReceipt",
    "CommitReceipt",
]
