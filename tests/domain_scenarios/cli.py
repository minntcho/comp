from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable, Sequence

from tests.domain_scenarios.core import (
    DomainScenarioResult,
    ScenarioDefinition,
    assert_scenario_contract,
    run_scenario,
)
from tests.domain_scenarios.registry import registered_scenarios


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

    parser.print_help(sys.stderr)
    return 2


def render_scenario_summary(
    scenario: ScenarioDefinition,
    result: DomainScenarioResult,
) -> str:
    lines = [
        f"Scenario: {scenario.scenario_id}",
        f"Title: {scenario.title}",
        f"Status: {result.report.status}",
        f"Commit: {result.preparation.decision.status}",
        f"Projection: {'present' if result.projection is not None else 'absent'}",
        "",
        "Resolver steps:",
    ]
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
    return "\n".join(lines)


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
    return parser


def _render_scenario_list(scenarios: Iterable[ScenarioDefinition]) -> str:
    return "\n".join(
        f"{scenario.scenario_id}\t{scenario.title}"
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


__all__ = ["main", "render_scenario_summary"]
