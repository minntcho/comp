from __future__ import annotations

import time

from comp.persistence import (
    ArtifactEnvelope,
    InMemoryArtifactStore,
    InMemoryReceiptLedger,
    ProjectionReplayBlocked,
    ReceiptLedgerKey,
    replay_public_projection,
)
from comp.scenario_contracts.case import RuntimeCase
from comp.scenario_contracts.invariants import evaluate_invariants
from comp.scenario_contracts.result import ScenarioResult


class TrustRuntime:
    """Narrow runtime for prepared trust inputs, not product ingestion."""

    def __init__(
        self,
        *,
        artifact_store: InMemoryArtifactStore | None = None,
        receipt_ledger: InMemoryReceiptLedger | None = None,
    ):
        self.artifact_store = (
            artifact_store if artifact_store is not None else InMemoryArtifactStore()
        )
        self.receipt_ledger = (
            receipt_ledger if receipt_ledger is not None else InMemoryReceiptLedger()
        )

    def run(
        self,
        *,
        scenario_id: str,
        runtime_case: RuntimeCase,
        artifact_envelopes: tuple[ArtifactEnvelope, ...],
        invariants: tuple[str, ...],
    ) -> ScenarioResult:
        started = time.perf_counter()
        for envelope in artifact_envelopes:
            self.artifact_store.record(envelope)
        receipt_keys: set[ReceiptLedgerKey] = set()
        for receipt in runtime_case.receipts:
            self.receipt_ledger.record(receipt)
            receipt_keys.add(ReceiptLedgerKey.from_receipt(receipt))

        replay_checked_count = 0
        replay_failed_count = 0
        for projection in runtime_case.projections:
            try:
                receipt = self.receipt_ledger.get(
                    public_row_id=projection.public_row_id,
                    projection_id=projection.projection_id,
                    draft_id=projection.draft_id,
                )
                replay_public_projection(
                    projection.row,
                    projection.projection_spec,
                    receipt=receipt,
                    artifacts=self.artifact_store,
                )
            except (KeyError, ProjectionReplayBlocked):
                replay_failed_count += 1
            else:
                replay_checked_count += 1

        invariant_results = evaluate_invariants(
            invariants,
            runtime_case=runtime_case,
            receipt_keys=receipt_keys,
            replay_checked_count=replay_checked_count,
            replay_failed_count=replay_failed_count,
        )
        status = (
            "passed"
            if all(result.status == "passed" for result in invariant_results)
            else "failed"
        )
        return ScenarioResult(
            scenario_id=scenario_id,
            status=status,
            artifact_count=len(artifact_envelopes),
            receipt_count=len(runtime_case.receipts),
            public_row_count=len(runtime_case.projections),
            replay_checked_count=replay_checked_count,
            replay_failed_count=replay_failed_count,
            invariant_results=invariant_results,
            performance={"runtime_sec": round(time.perf_counter() - started, 6)},
        )


__all__ = ["TrustRuntime"]
