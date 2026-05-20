from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from comp.compiler_tool import (
    CommitPreparation,
    CompileReport,
    commit_preparation_to_facts,
    compile_report_to_facts,
)
from comp.judgment import Fact, SubjectRef


@dataclass(frozen=True)
class SourceRef:
    repo: str
    path: str
    commit: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "repo": self.repo,
            "commit": self.commit,
            "path": self.path,
        }


@dataclass(frozen=True)
class ScenarioContract:
    must_commit: bool = False
    required_projection: Mapping[str, Any] | None = None
    required_resolved_obligation_kinds: tuple[str, ...] = ()
    required_reference_candidate_ids: tuple[str, ...] = ()
    required_reference_binding_ids: tuple[str, ...] = ()
    required_derived_claim_ids: tuple[str, ...] = ()
    required_receipt_reference_binding_ids: tuple[str, ...] = ()
    required_receipt_derived_claim_ids: tuple[str, ...] = ()
    required_receipt_calculation_trace_ids: tuple[str, ...] = ()
    required_receipt_formula_ids: tuple[str, ...] = ()
    required_open_obligation_ids: tuple[str, ...] | None = ()
    required_hazard_ids: tuple[str, ...] | None = ()


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    title: str
    run: Callable[[], "DomainScenarioResult"]
    contract: ScenarioContract
    source_refs: tuple[SourceRef, ...] = ()


@dataclass(frozen=True)
class DomainScenarioResult:
    scenario_id: str
    report: CompileReport
    preparation: CommitPreparation
    projection: dict[str, Any] | None
    report_facts: frozenset[Fact]
    commit_facts: frozenset[Fact]
    resolver_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        from tests.domain_scenarios.views import scenario_result_view

        return scenario_result_view(self)

    def to_json(self) -> str:
        return json.dumps(_json_ready(self.to_dict()), indent=2, sort_keys=True)


def build_domain_scenario_result(
    *,
    scenario_id: str,
    report: CompileReport,
    preparation: CommitPreparation,
    projection: dict[str, Any] | None,
    subject: SubjectRef,
    resolver_steps: tuple[str, ...],
) -> DomainScenarioResult:
    return DomainScenarioResult(
        scenario_id=scenario_id,
        report=report,
        preparation=preparation,
        projection=projection,
        report_facts=frozenset(compile_report_to_facts(report, subject)),
        commit_facts=frozenset(commit_preparation_to_facts(preparation, subject)),
        resolver_steps=resolver_steps,
    )


def run_scenario(scenario: ScenarioDefinition) -> DomainScenarioResult:
    result = scenario.run()
    if result.scenario_id != scenario.scenario_id:
        raise AssertionError(
            f"scenario result id {result.scenario_id!r} did not match "
            f"definition id {scenario.scenario_id!r}"
        )
    return result


def assert_scenario_contract(
    result: DomainScenarioResult,
    contract: ScenarioContract,
) -> None:
    if contract.must_commit:
        assert result.preparation.package.complete is True
        assert result.preparation.decision.status == "commit"
        assert result.preparation.receipt is not None

    if contract.required_projection is not None:
        assert result.projection is not None
        for key, expected in contract.required_projection.items():
            assert result.projection[key] == expected

    assert _contains_in_order(
        tuple(item.kind for item in result.report.resolved_obligations),
        contract.required_resolved_obligation_kinds,
    )
    assert _contains_in_order(
        tuple(
            candidate.reference_id
            for candidate in result.report.reference_candidates
        ),
        contract.required_reference_candidate_ids,
    )
    assert _contains_in_order(
        tuple(binding.binding_id for binding in result.report.reference_bindings),
        contract.required_reference_binding_ids,
    )
    assert _contains_in_order(
        tuple(claim.claim_id for claim in result.report.derived_claims),
        contract.required_derived_claim_ids,
    )

    citations = (
        result.preparation.receipt.citations
        if result.preparation.receipt is not None
        else None
    )
    if _requires_receipt_citations(contract):
        assert citations is not None
        assert _contains_in_order(
            citations.reference_binding_ids,
            contract.required_receipt_reference_binding_ids,
        )
        assert _contains_in_order(
            citations.derived_claim_ids,
            contract.required_receipt_derived_claim_ids,
        )
        assert _contains_in_order(
            citations.calculation_trace_ids,
            contract.required_receipt_calculation_trace_ids,
        )
        assert _contains_in_order(
            citations.formula_ids,
            contract.required_receipt_formula_ids,
        )

    if contract.required_open_obligation_ids is not None:
        assert (
            result.preparation.package.open_obligation_ids
            == contract.required_open_obligation_ids
        )
    if contract.required_hazard_ids is not None:
        assert result.preparation.package.hazard_ids == contract.required_hazard_ids


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value


def _contains_in_order(
    actual: tuple[Any, ...],
    expected: tuple[Any, ...],
) -> bool:
    if not expected:
        return True
    cursor = 0
    for item in actual:
        if item == expected[cursor]:
            cursor += 1
            if cursor == len(expected):
                return True
    return False


def _requires_receipt_citations(contract: ScenarioContract) -> bool:
    return any(
        (
            contract.required_receipt_reference_binding_ids,
            contract.required_receipt_derived_claim_ids,
            contract.required_receipt_calculation_trace_ids,
            contract.required_receipt_formula_ids,
        )
    )


__all__ = [
    "DomainScenarioResult",
    "ScenarioContract",
    "ScenarioDefinition",
    "SourceRef",
    "assert_scenario_contract",
    "build_domain_scenario_result",
    "run_scenario",
]
