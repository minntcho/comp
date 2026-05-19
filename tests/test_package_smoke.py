from pathlib import Path
import tomllib

import comp
from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    Fact,
    FixpointEngine,
    JudgmentState,
    SelectionReceipt,
    SubjectRef,
)

LEGACY_ACTIVE_PATHS = (
    "artifacts.py",
    "ast_builder.py",
    "ast_nodes.py",
    "binder.py",
    "calculation_pass.py",
    "compiled_expr_eval.py",
    "compiled_pipeline_runner.py",
    "compiled_spec.py",
    "emit_pass.py",
    "esg_builtins.py",
    "esgdl.lark",
    "expr_eval.py",
    "governance_pass.py",
    "inference_pass.py",
    "lex_eval.py",
    "lex_ir.py",
    "lex_pass.py",
    "lowering.py",
    "parse_pass.py",
    "pipeline_runner.py",
    "repair_pass.py",
    "rule_builtins.py",
    "rule_eval.py",
    "rule_ir.py",
    "runtime_env.py",
    "scope_resolution_pass.py",
    "semantic_pass.py",
    "source_eval.py",
    "source_ir.py",
    "spec_nodes.py",
    "comp/runner.py",
    "comp/builtins/__init__.py",
    "comp/compat/__init__.py",
    "comp/compat/artifacts.py",
    "comp/compat/compiled_spec.py",
    "comp/dsl/__init__.py",
    "comp/dsl/esgdl.lark",
    "comp/eval/__init__.py",
    "comp/pipeline/__init__.py",
)


def test_top_level_package_exposes_active_judgment_surface():
    assert Fact is not None
    assert JudgmentState is not None
    assert SubjectRef is not None
    assert FixpointEngine is not None
    assert SelectionReceipt is not None
    assert CommitReceipt is not None
    assert CommitReceiptCitations is not None


def test_top_level_package_no_longer_exports_legacy_runner_surface():
    assert not hasattr(comp, "ESGPipelineRunner")
    assert not hasattr(comp, "CompiledESGPipelineRunner")
    assert not hasattr(comp, "PipelineResources")
    assert not hasattr(comp, "PipelineRunResult")


def test_pyproject_packages_comp_core_and_agent_layer():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert pyproject["project"]["description"] == (
        "Receipt-gated proof package compiler for obligation, reference, "
        "calculation, and commit workflows"
    )

    setuptools_config = pyproject["tool"]["setuptools"]
    assert setuptools_config["packages"] == [
        "comp",
        "comp.compiler_tool",
        "comp.judgment",
        "minchoagnt",
    ]
    assert "py-modules" not in setuptools_config

    scripts = pyproject["project"].get("scripts", {})
    assert scripts["minchoagnt"] == "minchoagnt.cli:main"

    dependencies = pyproject["project"].get("dependencies", [])
    assert not any(dependency.startswith("lark") for dependency in dependencies)


def test_legacy_pipeline_sources_are_not_active_files():
    assert not [path for path in LEGACY_ACTIVE_PATHS if Path(path).exists()]
    assert "comp.runner" not in (comp.__doc__ or "")


def test_comp_core_does_not_import_agent_layer():
    comp_sources = Path("comp").rglob("*.py")
    assert not [
        path
        for path in comp_sources
        if "minchoagnt" in path.read_text(encoding="utf-8")
    ]
