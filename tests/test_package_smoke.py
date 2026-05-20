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


def test_readme_compiler_tool_import_surface_is_exported():
    from comp.compiler_tool import (
        CompileReport,
        CompilerTool,
        EmbeddingResolverStub,
        ReferenceIndexEntry,
        ReferenceQuery,
        ReferenceResolver,
        resolve_reference_retrieval_obligations,
        build_commit_receipt,
        compile_report_to_facts,
        prepare_commit,
        resolver_tasks_from_report,
    )

    assert CompilerTool is not None
    assert CompileReport is not None
    assert resolver_tasks_from_report is not None
    assert prepare_commit is not None
    assert build_commit_receipt is not None
    assert compile_report_to_facts is not None
    assert ReferenceQuery is not None
    assert ReferenceIndexEntry is not None
    assert ReferenceResolver is not None
    assert EmbeddingResolverStub is not None
    assert resolve_reference_retrieval_obligations is not None


def test_working_theory_status_section_tracks_current_rebuild_state():
    working_theory = Path(
        "docs/architecture/obligation-kernel-working-theory.md"
    ).read_text(encoding="utf-8")

    assert "## 13. Current Implementation Status" in working_theory
    assert "SemanticJudgment obligation validation" in working_theory
    assert "ReferenceCandidate / ReferenceBinding" in working_theory
    assert "CommitPackage / GovernanceDecision / CommitReceipt" in working_theory
    assert "Domain Scenario Lab" in working_theory
    assert "Retrieval lens interface" in working_theory
    assert "EmbeddingResolverStub" in working_theory
    assert "retrieval resolver bridge" in working_theory
    assert "resolve only the search obligation" in working_theory.lower()
    assert "PR8: Core / Domain Boundary Working Theory" not in working_theory
    assert "PR9: SemanticJudgmentObligation Minimal Slice" not in working_theory


def test_domain_scenario_generation_guide_tracks_swappable_pack_contract():
    guide = Path(
        "docs/architecture/domain-scenario-pack-generation.md"
    ).read_text(encoding="utf-8")

    assert "Scenario Pack" in guide
    assert "ScenarioDefinition" in guide
    assert "ScenarioContract" in guide
    assert "SourceRef" in guide
    assert "registered_scenarios()" in guide
    assert "Do not assert one huge exported JSON blob" in guide
    assert "minntcho/esg-platform" in guide


def test_pyproject_packages_comp_core_and_agent_layer():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    from comp.persistence import (
        ArtifactEnvelope,
        InMemoryArtifactStore,
        InMemoryReceiptLedger,
        artifact_digest,
        verify_materialized_public_projection,
    )

    assert pyproject["project"]["description"] == (
        "Receipt-gated proof package compiler for obligation, reference, "
        "calculation, and commit workflows"
    )

    setuptools_config = pyproject["tool"]["setuptools"]
    assert setuptools_config["packages"] == [
        "comp",
        "comp.compiler_tool",
        "comp.judgment",
        "comp.persistence",
        "minchoagnt",
    ]
    assert "py-modules" not in setuptools_config

    scripts = pyproject["project"].get("scripts", {})
    assert scripts["minchoagnt"] == "minchoagnt.cli:main"

    dependencies = pyproject["project"].get("dependencies", [])
    assert not any(dependency.startswith("lark") for dependency in dependencies)
    assert ArtifactEnvelope is not None
    assert InMemoryArtifactStore is not None
    assert InMemoryReceiptLedger is not None
    assert artifact_digest is not None
    assert verify_materialized_public_projection is not None


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
