from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from comp.scenario_contracts import load_manifest, run_scenario
from comp.scenario_contracts import write_public_projection_smoke_bundle


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command != "scenario":
        parser.print_help(sys.stderr)
        return 2
    if args.scenario_command == "validate":
        manifest = load_manifest(args.manifest)
        print(f"{manifest.scenario_id}: valid")
        return 0
    if args.scenario_command == "run":
        result = run_scenario(args.manifest, report_path=args.report)
        print(f"{result.scenario_id}: {result.status}")
        return 0 if result.status == "passed" else 1
    if args.scenario_command == "init":
        manifest_path = write_public_projection_smoke_bundle(args.target)
        print(f"created {manifest_path}")
        return 0
    parser.print_help(sys.stderr)
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="comp")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scenario = subparsers.add_parser("scenario", help="Run public scenario contracts.")
    scenario_subparsers = scenario.add_subparsers(
        dest="scenario_command",
        required=True,
    )
    validate = scenario_subparsers.add_parser(
        "validate",
        help="Validate a prepared scenario manifest.",
    )
    validate.add_argument("manifest")
    run = scenario_subparsers.add_parser(
        "run",
        help="Run a prepared scenario through the trust path.",
    )
    run.add_argument("manifest")
    run.add_argument("--report")
    init = scenario_subparsers.add_parser(
        "init",
        help="Create a runnable public-projection smoke scenario bundle.",
    )
    init.add_argument("target")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
