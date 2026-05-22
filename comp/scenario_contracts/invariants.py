from __future__ import annotations

from collections.abc import Mapping

from comp.persistence.ledger import ReceiptLedgerKey
from comp.scenario_contracts.case import RuntimeCase
from comp.scenario_contracts.result import InvariantResult


def evaluate_invariants(
    names: tuple[str, ...],
    *,
    runtime_case: RuntimeCase,
    receipt_keys: set[ReceiptLedgerKey],
    replay_checked_count: int,
    replay_failed_count: int,
) -> tuple[InvariantResult, ...]:
    evaluators = {
        "receipt_exists": _receipt_exists,
        "all_public_rows_have_receipts": _all_public_rows_have_receipts,
        "replay_succeeds": _replay_succeeds,
        "projection_values_are_committed": _replay_succeeds,
        "blocking_hazards_absent": _blocking_hazards_absent,
    }
    context = {
        "runtime_case": runtime_case,
        "receipt_keys": receipt_keys,
        "replay_checked_count": replay_checked_count,
        "replay_failed_count": replay_failed_count,
    }
    results: list[InvariantResult] = []
    for name in names:
        evaluator = evaluators.get(name)
        if evaluator is None:
            results.append(
                InvariantResult(name=name, status="failed", message="unknown invariant")
            )
            continue
        results.append(evaluator(name, context))
    return tuple(results)


def _receipt_exists(name: str, context: Mapping[str, object]) -> InvariantResult:
    runtime_case = _runtime_case(context)
    receipt_keys = _receipt_keys(context)
    missing = [
        projection.receipt_key
        for projection in runtime_case.projections
        if projection.receipt_key not in receipt_keys
    ]
    if missing:
        return InvariantResult(name=name, status="failed", message="missing receipt")
    return InvariantResult(name=name, status="passed")


def _all_public_rows_have_receipts(
    name: str,
    context: Mapping[str, object],
) -> InvariantResult:
    return _receipt_exists(name, context)


def _replay_succeeds(name: str, context: Mapping[str, object]) -> InvariantResult:
    replay_checked_count = int(context["replay_checked_count"])
    replay_failed_count = int(context["replay_failed_count"])
    runtime_case = _runtime_case(context)
    if replay_failed_count:
        return InvariantResult(name=name, status="failed", message="replay failed")
    if replay_checked_count != len(runtime_case.projections):
        return InvariantResult(name=name, status="failed", message="replay incomplete")
    return InvariantResult(name=name, status="passed")


def _blocking_hazards_absent(
    name: str,
    context: Mapping[str, object],
) -> InvariantResult:
    runtime_case = _runtime_case(context)
    for receipt in runtime_case.receipts:
        citations = receipt.citations
        if citations is not None and citations.hazard_ids:
            return InvariantResult(
                name=name,
                status="failed",
                message="blocking hazards present",
            )
    return InvariantResult(name=name, status="passed")


def _runtime_case(context: Mapping[str, object]) -> RuntimeCase:
    runtime_case = context["runtime_case"]
    assert isinstance(runtime_case, RuntimeCase)
    return runtime_case


def _receipt_keys(context: Mapping[str, object]) -> set[ReceiptLedgerKey]:
    receipt_keys = context["receipt_keys"]
    assert isinstance(receipt_keys, set)
    return receipt_keys


__all__ = ["evaluate_invariants"]
