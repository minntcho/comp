"""Active package surface for the comp rebuild branch.

The top-level package intentionally exposes the judgment-core surface only.
Legacy pipeline runners and pass-pipeline modules live in the archive snapshot;
they are no longer active package source.
"""

from comp.judgment import (
    BundleSpec,
    CandidateSummary,
    CommitReceipt,
    CommitSpec,
    CompiledJudgmentProgram,
    DraftSnapshot,
    Fact,
    FactTag,
    FixpointEngine,
    JudgmentState,
    ProjectionSpec,
    SelectionReceipt,
    SubjectKind,
    SubjectRef,
    TransferEmitter,
    TransferRule,
    blocking_hazards_clear,
    committable,
    dominates,
    frontier,
    needs_review,
    project_public_row,
    prov_enough,
    resolved_required_bundles,
    winner_or_none,
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
