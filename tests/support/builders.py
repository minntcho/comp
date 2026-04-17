from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from runtime_env import ScopeFrame, SiteRecord


@dataclass
class TestFragment:
    fragment_id: str
    fragment_type: str
    text: str
    scope_path: tuple[ScopeFrame, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestResources:
    site_records: list[SiteRecord] = field(default_factory=list)
    factor_rows: list[dict[str, Any]] = field(default_factory=list)
    policy_flags: dict[str, Any] = field(default_factory=dict)
    activity_aliases: dict[str, list[str]] = field(default_factory=dict)
    unit_aliases: dict[str, list[str]] = field(default_factory=dict)


def make_scope_path(*, doc: str = "doc:1", section: str = "sec:1", table: str = "tbl:1", row: str = "row:1") -> tuple[ScopeFrame, ...]:
    return (
        ScopeFrame(level="document", ref_id=doc),
        ScopeFrame(level="section", ref_id=section),
        ScopeFrame(level="table", ref_id=table),
        ScopeFrame(level="row", ref_id=row),
    )


def make_fragment(
    *,
    fragment_id: str,
    text: str,
    fragment_type: str = "line",
    scope_path: tuple[ScopeFrame, ...] | None = None,
    metadata: dict[str, Any] | None = None,
) -> TestFragment:
    return TestFragment(
        fragment_id=fragment_id,
        fragment_type=fragment_type,
        text=text,
        scope_path=scope_path or make_scope_path(),
        metadata=metadata or {},
    )


def make_resources(
    *,
    site_records: Iterable[SiteRecord] | None = None,
    factor_rows: Iterable[dict[str, Any]] | None = None,
    policy_flags: dict[str, Any] | None = None,
    activity_aliases: dict[str, list[str]] | None = None,
    unit_aliases: dict[str, list[str]] | None = None,
) -> object:
    return TestResources(
        site_records=list(site_records or []),
        factor_rows=list(factor_rows or []),
        policy_flags=dict(policy_flags or {}),
        activity_aliases=dict(activity_aliases or {}),
        unit_aliases=dict(unit_aliases or {}),
    )


def run_pipeline_full(*, dsl_text: str, fragments: list[TestFragment], resources: object):
    from pipeline_runner import ESGPipelineRunner

    runner = ESGPipelineRunner(grammar_path="esgdl.lark")
    return runner.run(dsl_text=dsl_text, fragments=fragments, resources=resources)


def run_pipeline_until(
    *,
    dsl_text: str,
    fragments: list[TestFragment],
    resources: object,
    pass_name: str,
):
    from pipeline_runner import ESGPipelineRunner, build_default_passes

    selected = []
    for compiler_pass in build_default_passes():
        selected.append(compiler_pass)
        if compiler_pass.__class__.__name__ == pass_name:
            break

    if not selected or selected[-1].__class__.__name__ != pass_name:
        raise ValueError(f"unknown pass_name: {pass_name}")

    runner = ESGPipelineRunner(grammar_path="esgdl.lark", passes=selected)
    return runner.run(dsl_text=dsl_text, fragments=fragments, resources=resources)
