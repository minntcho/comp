from pathlib import Path
import tomllib

import comp
from comp import (
    CommitReceipt,
    CommitReceiptCitations,
    DependencyFingerprint,
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
    assert DependencyFingerprint is not None


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
        ReferenceCatalogSnapshot,
        RetrievalQueryPolicy,
        RetrievalQueryRule,
        active_retrieval_query_policies,
        calculation_formula_declaration_fingerprint,
        domain_pack_declaration_fingerprint,
        evidence_witness_fingerprint,
        profile_declaration_fingerprint,
        reference_catalog_snapshot_fingerprint,
        reference_query_for_obligation_from_profile_policy,
        reference_query_for_obligation_from_policies,
        reference_query_for_obligation_from_policy,
        reference_query_for_obligation_from_resolver_tasks,
        reference_query_from_resolver_task,
        reference_record_fingerprint,
        resolve_reference_retrieval_obligations,
        rule_family_declaration_fingerprint,
        semantic_rubric_declaration_fingerprint,
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
    assert ReferenceCatalogSnapshot is not None
    assert EmbeddingResolverStub is not None
    assert RetrievalQueryPolicy is not None
    assert RetrievalQueryRule is not None
    assert calculation_formula_declaration_fingerprint is not None
    assert domain_pack_declaration_fingerprint is not None
    assert evidence_witness_fingerprint is not None
    assert active_retrieval_query_policies is not None
    assert profile_declaration_fingerprint is not None
    assert reference_query_for_obligation_from_policies is not None
    assert reference_query_for_obligation_from_profile_policy is not None
    assert reference_query_for_obligation_from_policy is not None
    assert reference_query_from_resolver_task is not None
    assert reference_query_for_obligation_from_resolver_tasks is not None
    assert reference_catalog_snapshot_fingerprint is not None
    assert reference_record_fingerprint is not None
    assert rule_family_declaration_fingerprint is not None
    assert semantic_rubric_declaration_fingerprint is not None
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


def test_document_governance_classifies_architecture_doc_authority():
    governance = Path(
        "docs/architecture/document-governance.md"
    ).read_text(encoding="utf-8")
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    assert "Status: active-contract" in governance
    assert "Can block PRs: yes" in governance
    assert "Active Contract" in governance
    assert "Implementation Map" in governance
    assert "North Star" in governance
    assert "Historical / Exploratory Note" in governance
    assert "Can this document block a PR?" in governance
    assert "document-governance.md" in docs_index

    required_headers = {
        "docs/architecture/trust-kernel-extension-rings.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/persistence-ledger-boundary.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/artifact-envelope-builder.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/retrieval-fabric-north-star.md": (
            "Status: north-star",
            "Can block PRs: limited",
        ),
        "docs/architecture/obligation-kernel-working-theory.md": (
            "Status: implementation-map",
            "Can block PRs: limited",
        ),
        "docs/architecture/domain-scenario-pack-generation.md": (
            "Status: implementation-map",
            "Can block PRs: limited",
        ),
    }
    for path, expected_lines in required_headers.items():
        text = Path(path).read_text(encoding="utf-8")
        for line in expected_lines:
            assert line in text


def test_architecture_docs_are_classified_by_governance_status():
    expected_status = {
        "active-surface-cutover.md": ("historical-note", "docs", "no"),
        "artifact-envelope-builder.md": ("active-contract", "persistence", "yes"),
        "document-governance.md": ("active-contract", "trust-kernel", "yes"),
        "domain-scenario-pack-generation.md": (
            "implementation-map",
            "scenario-lab",
            "limited",
        ),
        "extension-port-contracts.md": ("active-contract", "trust-kernel", "yes"),
        "legacy-archive-cutover-plan.md": ("historical-note", "docs", "no"),
        "llm-orchestrated-compiler-tool-loop.md": (
            "historical-note",
            "agent-layer",
            "no",
        ),
        "llm-worker-orchestration.md": ("north-star", "agent-layer", "limited"),
        "memory-assisted-compiler-loop.md": (
            "active-contract",
            "agent-layer",
            "yes",
        ),
        "obligation-kernel-working-theory.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
        ),
        "persistence-ledger-boundary.md": ("active-contract", "persistence", "yes"),
        "receipt-proof-graph.md": ("active-contract", "explanation", "yes"),
        "retrieval-fabric-north-star.md": ("north-star", "retrieval", "limited"),
        "trust-kernel-extension-rings.md": ("active-contract", "trust-kernel", "yes"),
        "trust-kernel-hardening.md": ("active-contract", "trust-kernel", "yes"),
    }

    architecture_docs = sorted(Path("docs/architecture").glob("*.md"))
    assert {path.name for path in architecture_docs} == set(expected_status)

    for path in architecture_docs:
        status, owner, blocking = expected_status[path.name]
        text = path.read_text(encoding="utf-8")
        assert f"Status: {status}" in text
        assert f"Owner: {owner}" in text
        assert "Last checked against code: 2026-05-20" in text
        assert f"Can block PRs: {blocking}" in text


def test_docs_index_groups_architecture_docs_by_governance_authority():
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    for heading in (
        "### Active Contracts",
        "### Implementation Maps",
        "### North Stars",
        "### Historical Notes",
    ):
        assert heading in docs_index

    assert docs_index.index("### Active Contracts") < docs_index.index(
        "### Implementation Maps"
    )
    assert docs_index.index("### Implementation Maps") < docs_index.index(
        "### North Stars"
    )
    assert docs_index.index("### North Stars") < docs_index.index(
        "### Historical Notes"
    )
    assert "architecture/active-surface-cutover.md" in docs_index
    assert "architecture/legacy-archive-cutover-plan.md" in docs_index
    assert "architecture/llm-orchestrated-compiler-tool-loop.md" in docs_index


def test_pyproject_packages_comp_core_and_agent_layer():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    from comp.persistence import (
        ArtifactEnvelope,
        ArtifactRef,
        InMemoryArtifactStore,
        InMemoryReceiptLedger,
        ProjectionReplayReport,
        artifact_digest,
        replay_public_projection,
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
    assert ArtifactRef is not None
    assert InMemoryArtifactStore is not None
    assert InMemoryReceiptLedger is not None
    assert ProjectionReplayReport is not None
    assert artifact_digest is not None
    assert replay_public_projection is not None
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
