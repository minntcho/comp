from __future__ import annotations

import json
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
class DomainScenarioResult:
    scenario_id: str
    report: CompileReport
    preparation: CommitPreparation
    projection: dict[str, Any] | None
    report_facts: frozenset[Fact]
    commit_facts: frozenset[Fact]
    resolver_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "resolver_steps": self.resolver_steps,
            "report": {
                "status": self.report.status,
                "open_obligations": [
                    _obligation_view(obligation)
                    for obligation in self.report.obligations
                ],
                "resolved_obligations": [
                    _obligation_view(obligation)
                    for obligation in self.report.resolved_obligations
                ],
                "reference_candidates": [
                    {
                        "candidate_id": candidate.candidate_id,
                        "reference_id": candidate.reference_id,
                        "reference_type": candidate.reference_type,
                        "retrieval_method": candidate.retrieval_method,
                        "retrieval_score": candidate.retrieval_score,
                        "authority": candidate.authority,
                    }
                    for candidate in self.report.reference_candidates
                ],
                "reference_bindings": [
                    {
                        "binding_id": binding.binding_id,
                        "reference_id": binding.reference_id,
                        "selected_candidate_id": binding.selected_candidate_id,
                        "rejected_candidates": [
                            {
                                "reference_id": rejected.reference_id,
                                "reason": rejected.reason,
                            }
                            for rejected in binding.rejected_candidates
                        ],
                    }
                    for binding in self.report.reference_bindings
                ],
                "derived_claims": [
                    {
                        "claim_id": claim.claim_id,
                        "field": claim.field,
                        "value": claim.value,
                        "unit": claim.unit,
                        "trace_id": claim.trace.trace_id,
                        "formula_id": claim.formula_id,
                        "reference_binding_ids": claim.trace.reference_binding_ids,
                    }
                    for claim in self.report.derived_claims
                ],
            },
            "commit": {
                "package_id": self.preparation.package.package_id,
                "package_complete": self.preparation.package.complete,
                "governance_status": self.preparation.decision.status,
                "receipt_id": (
                    self.preparation.receipt.public_row_id
                    if self.preparation.receipt is not None
                    else None
                ),
            },
            "facts": {
                "report_count": len(self.report_facts),
                "commit_count": len(self.commit_facts),
            },
            "projection": self.projection,
        }

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


def _obligation_view(obligation) -> dict[str, str | None]:
    return {
        "obligation_id": obligation.obligation_id,
        "kind": obligation.kind,
        "field": obligation.field,
        "reason": obligation.reason,
    }


def _json_ready(value):
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    return value


__all__ = ["DomainScenarioResult", "build_domain_scenario_result"]
