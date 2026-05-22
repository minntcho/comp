from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioDefinition,
    assert_scenario_contract,
    run_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios, scenario_residency


@dataclass(frozen=True)
class ScenarioRunStatus:
    scenario: ScenarioDefinition
    result: DomainScenarioResult | None
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        print(_render_scenario_list(registered_scenarios()))
        return 0

    if args.command == "run":
        scenario = _find_scenario(args.scenario_id)
        if scenario is None:
            print(_unknown_scenario_message(args.scenario_id), file=sys.stderr)
            return 2

        result = run_scenario(scenario)
        assert_scenario_contract(result, scenario.contract)
        if args.json:
            print(result.to_json())
        else:
            print(render_scenario_summary(scenario, result))
        return 0

    if args.command == "run-all":
        statuses = run_all_scenarios()
        if args.json:
            print(render_run_all_json(statuses))
        else:
            print(render_run_all_summary(statuses))
        return 0 if all(status.passed for status in statuses) else 1

    parser.print_help(sys.stderr)
    return 2


def run_all_scenarios() -> tuple[ScenarioRunStatus, ...]:
    statuses: list[ScenarioRunStatus] = []
    for scenario in registered_scenarios():
        try:
            result = run_scenario(scenario)
            assert_scenario_contract(result, scenario.contract)
        except AssertionError as exc:
            statuses.append(
                ScenarioRunStatus(
                    scenario=scenario,
                    result=None,
                    error=str(exc) or exc.__class__.__name__,
                )
            )
        else:
            statuses.append(ScenarioRunStatus(scenario=scenario, result=result))
    return tuple(statuses)


def render_run_all_summary(statuses: Sequence[ScenarioRunStatus]) -> str:
    passed = sum(1 for status in statuses if status.passed)
    lines = [
        "Domain Scenario Run",
        f"Passed: {passed}/{len(statuses)}",
        "",
        "Scenarios:",
    ]
    for status in statuses:
        label = "pass" if status.passed else "fail"
        detail = _run_status_detail(status)
        lines.append(f"- {status.scenario.scenario_id}: {label}{detail}")
    return "\n".join(lines)


def render_run_all_json(statuses: Sequence[ScenarioRunStatus]) -> str:
    passed = sum(1 for status in statuses if status.passed)
    payload = {
        "summary": {
            "total": len(statuses),
            "passed": passed,
            "failed": len(statuses) - passed,
        },
        "scenarios": [_run_status_payload(status) for status in statuses],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def render_scenario_summary(
    scenario: ScenarioDefinition,
    result: DomainScenarioResult,
) -> str:
    from comp.views import validation_summary_view

    validation_summary = validation_summary_view(result.report)
    lines = [
        f"Scenario: {scenario.scenario_id}",
        f"Title: {scenario.title}",
        f"Status: {result.report.status}",
        f"Commit: {result.preparation.decision.status}",
        f"Public output: {'present' if result.projection is not None else 'absent'}",
        "",
    ]
    lines.extend(_render_validation_summary_lines(validation_summary))
    lines.append("Resolver steps:")
    lines.extend(f"- {step}" for step in result.resolver_steps)
    lines.extend(
        (
            "",
            "Receipt trace:",
        )
    )

    citations = (
        result.preparation.receipt.citations
        if result.preparation.receipt is not None
        else None
    )
    if citations is None:
        lines.append("- receipt citations: absent")
    else:
        lines.extend(
            (
                f"- reference bindings: {len(citations.reference_binding_ids)}",
                f"- derived claims: {len(citations.derived_claim_ids)}",
                f"- calculation traces: {len(citations.calculation_trace_ids)}",
                f"- formulas: {len(citations.formula_ids)}",
            )
        )
    lines.extend(
        (
            "",
            "Replay trace:",
        )
    )
    replay_trace = result.to_dict().get("replay_trace")
    if replay_trace is None:
        lines.append("- status: absent")
    else:
        lines.extend(
            (
                f"- status: {replay_trace['status']}",
                f"- artifacts: {len(replay_trace.get('artifact_refs', ()))}",
                f"- dependency manifests: {_dependency_manifest_count(replay_trace)}",
            )
        )
    return "\n".join(lines)


def _render_validation_summary_lines(summary: dict[str, Any]) -> list[str]:
    public_output = summary["public_output"]
    open_requirements = summary["open_requirements"]
    lines = [
        "Validation summary:",
        f"- {summary['label_ko']}: {summary['status_ko']}",
        f"- {public_output['label_ko']}: {public_output['state_ko']}",
    ]
    lines.extend(
        f"- {section['label_ko']}: {section['count']}"
        for section in summary["sections"]
    )
    lines.append(f"- 보완 필요 항목: {len(open_requirements)}")
    for requirement in open_requirements:
        lines.append(f"  - {requirement['field']}: {requirement['message_ko']}")
        action = requirement.get("action_ko")
        if action:
            lines.append(f"    조치: {action}")
    lines.append("")
    return lines


def _dependency_manifest_count(replay_trace: dict[str, object]) -> int:
    manifests = replay_trace.get("dependency_manifests")
    if not isinstance(manifests, dict):
        return 0
    return sum(
        len(items)
        for items in manifests.values()
        if isinstance(items, list)
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tests.domain_scenarios",
        description="Run registered Domain Scenario Lab packs.",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("list", help="List registered domain scenarios.")

    run = subparsers.add_parser("run", help="Run one registered domain scenario.")
    run.add_argument("scenario_id", help="Scenario id from the registry.")
    run.add_argument(
        "--json",
        action="store_true",
        help="Print the scenario result viewer payload as JSON.",
    )

    run_all = subparsers.add_parser(
        "run-all",
        help="Run all registered domain scenarios and assert their contracts.",
    )
    run_all.add_argument(
        "--json",
        action="store_true",
        help="Print an aggregate scenario run payload as JSON.",
    )
    return parser


def _render_scenario_list(scenarios: Iterable[ScenarioDefinition]) -> str:
    return "\n".join(
        f"{scenario.scenario_id}\t{scenario_residency(scenario.scenario_id).tier}"
        f"\t{scenario.title}"
        for scenario in scenarios
    )


def _find_scenario(scenario_id: str) -> ScenarioDefinition | None:
    for scenario in registered_scenarios():
        if scenario.scenario_id == scenario_id:
            return scenario
    return None


def _unknown_scenario_message(scenario_id: str) -> str:
    known = ", ".join(scenario.scenario_id for scenario in registered_scenarios())
    return f"unknown scenario id: {scenario_id}\nknown scenarios: {known}"


def _run_status_detail(status: ScenarioRunStatus) -> str:
    if not status.passed:
        return f" ({status.error})"
    assert status.result is not None
    projection = "projection" if status.result.projection is not None else "no projection"
    return (
        f" ({status.result.report.status}, "
        f"{status.result.preparation.decision.status}, {projection})"
    )


def _run_status_payload(status: ScenarioRunStatus) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "scenario_id": status.scenario.scenario_id,
        "title": status.scenario.title,
        "status": "pass" if status.passed else "fail",
    }
    if status.result is None:
        payload["error"] = status.error
    else:
        payload["result"] = status.result.to_dict()
    return payload


__all__ = [
    "ScenarioRunStatus",
    "main",
    "render_run_all_json",
    "render_run_all_summary",
    "render_scenario_summary",
    "run_all_scenarios",
]
