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
        CalculatedClaim,
        CanonicalReference,
        ClaimCandidate,
        CompileReport,
        CompilerTool,
        EvidenceRef,
        EmbeddingResolverStub,
        ReferenceIndexEntry,
        ReferenceQuery,
        ReferenceResolver,
        ReferenceCatalogSnapshot,
        ReviewDecision,
        ReviewPackage,
        RetrievalQueryPolicy,
        RetrievalQueryRule,
        active_retrieval_query_policies,
        calculation_formula_declaration_fingerprint,
        domain_pack_declaration_fingerprint,
        evidence_ref_fingerprint,
        evidence_witness_fingerprint,
        profile_declaration_fingerprint,
        profile_allowed_units,
        profile_known_fields,
        reference_catalog_snapshot_fingerprint,
        reference_query_for_obligation_from_profile_policy,
        reference_query_for_obligation_from_policies,
        reference_query_for_obligation_from_policy,
        reference_query_for_obligation_from_resolver_tasks,
        reference_query_from_resolver_task,
        reference_record_fingerprint,
        ReferenceOption,
        resolve_reference_retrieval_obligations,
        rule_family_declaration_fingerprint,
        semantic_rubric_declaration_fingerprint,
        ValidationRequirement,
        ValidationReport,
        build_commit_receipt,
        compile_report_to_facts,
        prepare_commit,
        resolver_tasks_from_report,
    )

    assert CalculatedClaim is not None
    assert CanonicalReference is not None
    assert ClaimCandidate is not None
    assert CompilerTool is not None
    assert CompileReport is not None
    assert EvidenceRef is not None
    assert resolver_tasks_from_report is not None
    assert prepare_commit is not None
    assert build_commit_receipt is not None
    assert compile_report_to_facts is not None
    assert ReferenceQuery is not None
    assert ReferenceIndexEntry is not None
    assert ReferenceResolver is not None
    assert ReferenceCatalogSnapshot is not None
    assert ReviewDecision is not None
    assert ReviewPackage is not None
    assert EmbeddingResolverStub is not None
    assert RetrievalQueryPolicy is not None
    assert RetrievalQueryRule is not None
    assert calculation_formula_declaration_fingerprint is not None
    assert domain_pack_declaration_fingerprint is not None
    assert evidence_ref_fingerprint is not None
    assert evidence_witness_fingerprint is not None
    assert active_retrieval_query_policies is not None
    assert profile_declaration_fingerprint is not None
    assert profile_allowed_units is not None
    assert profile_known_fields is not None
    assert reference_query_for_obligation_from_policies is not None
    assert reference_query_for_obligation_from_profile_policy is not None
    assert reference_query_for_obligation_from_policy is not None
    assert reference_query_from_resolver_task is not None
    assert reference_query_for_obligation_from_resolver_tasks is not None
    assert ReferenceOption is not None
    assert reference_catalog_snapshot_fingerprint is not None
    assert reference_record_fingerprint is not None
    assert rule_family_declaration_fingerprint is not None
    assert semantic_rubric_declaration_fingerprint is not None
    assert ValidationRequirement is not None
    assert ValidationReport is not None
    assert resolve_reference_retrieval_obligations is not None


def test_readme_tracks_persistence_active_surface():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "comp.persistence" in readme
    assert "ArtifactEnvelope" in readme
    assert "replay_public_projection" in readme


def test_persistence_exports_mysql_backend_surface():
    from comp.persistence import (
        MySQLArtifactStore,
        MySQLReceiptLedger,
        apply_trust_spine_schema,
    )

    assert MySQLArtifactStore is not None
    assert MySQLReceiptLedger is not None
    assert apply_trust_spine_schema is not None


def test_trust_kernel_hardening_documents_projection_numeric_policy():
    hardening = Path("docs/architecture/trust-kernel-hardening.md").read_text(
        encoding="utf-8"
    )

    assert "## Projection Numeric Value Policy" in hardening
    assert "ProjectionValueCommitment" in hardening
    assert "Decimal" in hardening


def test_trust_kernel_hardening_documents_profile_baseline_policy():
    hardening = Path("docs/architecture/trust-kernel-hardening.md").read_text(
        encoding="utf-8"
    )

    assert "profile-declared baseline" in hardening
    assert "known fields and allowed units" in hardening
    assert "run_profile_rules" in hardening


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
    assert "media_type" in guide
    assert "schema_id" in guide
    assert "content_digest" in guide
    assert "synthetic_source_input" in guide
    assert "Oracle files remain test expectations" in guide
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
        "active-surface-cutover.md": (
            "historical-note",
            "docs",
            "no",
            "2026-05-20",
        ),
        "artifact-envelope-builder.md": (
            "active-contract",
            "persistence",
            "yes",
            "2026-05-20",
        ),
        "document-governance.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-20",
        ),
        "domain-scenario-pack-generation.md": (
            "implementation-map",
            "scenario-lab",
            "limited",
            "2026-05-21",
        ),
        "extension-port-contracts.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-20",
        ),
        "friendly-authority-vocabulary.md": (
            "north-star",
            "trust-kernel",
            "limited",
            "2026-05-22",
        ),
        "legacy-archive-cutover-plan.md": (
            "historical-note",
            "docs",
            "no",
            "2026-05-20",
        ),
        "llm-orchestrated-compiler-tool-loop.md": (
            "historical-note",
            "agent-layer",
            "no",
            "2026-05-20",
        ),
        "llm-worker-orchestration.md": (
            "north-star",
            "agent-layer",
            "limited",
            "2026-05-20",
        ),
        "memory-assisted-compiler-loop.md": (
            "active-contract",
            "agent-layer",
            "yes",
            "2026-05-20",
        ),
        "obligation-kernel-working-theory.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-20",
        ),
        "persistence-ledger-boundary.md": (
            "active-contract",
            "persistence",
            "yes",
            "2026-05-21",
        ),
        "production-trust-spine-database.md": (
            "north-star",
            "persistence",
            "limited",
            "2026-05-21",
        ),
        "receipt-proof-graph.md": (
            "active-contract",
            "explanation",
            "yes",
            "2026-05-20",
        ),
        "retrieval-fabric-north-star.md": (
            "north-star",
            "retrieval",
            "limited",
            "2026-05-20",
        ),
        "trust-kernel-extension-rings.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-20",
        ),
        "trust-kernel-hardening.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-21",
        ),
    }

    architecture_docs = sorted(Path("docs/architecture").glob("*.md"))
    assert {path.name for path in architecture_docs} == set(expected_status)

    for path in architecture_docs:
        status, owner, blocking, checked_date = expected_status[path.name]
        text = path.read_text(encoding="utf-8")
        assert f"Status: {status}" in text
        assert f"Owner: {owner}" in text
        assert f"Last checked against code: {checked_date}" in text
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
    assert "architecture/friendly-authority-vocabulary.md" in docs_index
    assert "architecture/legacy-archive-cutover-plan.md" in docs_index
    assert "architecture/llm-orchestrated-compiler-tool-loop.md" in docs_index
    assert "architecture/production-trust-spine-database.md" in docs_index


def test_friendly_authority_vocabulary_names_rename_path_without_moving_authority():
    vocabulary = Path(
        "docs/architecture/friendly-authority-vocabulary.md"
    ).read_text(encoding="utf-8")

    assert "Status: north-star" in vocabulary
    assert "ClaimHypothesis` | `ClaimCandidate" in vocabulary
    assert "EvidenceWitness` | `EvidenceRef" in vocabulary
    assert "ProofObligation` | `ValidationRequirement" in vocabulary
    assert "ReferenceBinding` | `CanonicalReference" in vocabulary
    assert "CommitReceipt` | `PublicOutputReceipt" in vocabulary
    assert "공개 승인 증표" in vocabulary
    assert "감사 산출물 기록" in vocabulary
    assert "Canonical rename with deprecated aliases" in vocabulary
    assert "ClaimCandidate is canonical." in vocabulary
    assert "CanonicalReference is canonical." in vocabulary
    assert "ValidationReport is canonical." in vocabulary
    assert "ReviewPackage is canonical." in vocabulary
    assert "ReviewDecision is canonical." in vocabulary
    assert "ProofObligation remains a compatibility alias." in vocabulary
    assert "Only a clean public-output receipt can authorize public output." in vocabulary


def test_production_database_north_star_is_provisional_and_discoverable():
    db_north_star = Path(
        "docs/architecture/production-trust-spine-database.md"
    ).read_text(encoding="utf-8")
    persistence_boundary = Path(
        "docs/architecture/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "Status: north-star" in db_north_star
    assert "not a final database schema" in db_north_star
    assert "intentionally provisional" in db_north_star
    assert "Expected to evolve" in db_north_star
    assert "production-trust-spine-database.md" in persistence_boundary


def test_production_database_north_star_tracks_v1_mysql_spine():
    db_doc = Path(
        "docs/architecture/production-trust-spine-database.md"
    ).read_text(encoding="utf-8")
    persistence_doc = Path(
        "docs/architecture/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "## 12. Current Implementation Status" in db_doc
    assert "MySQLArtifactStore" in db_doc
    assert "MySQLReceiptLedger" in db_doc
    assert "ledger_receipt_artifact_refs" in db_doc
    assert "MySQL trust spine" in persistence_doc


def test_receipt_proof_graph_contract_names_prework_boundaries():
    graph_doc = Path("docs/architecture/receipt-proof-graph.md").read_text(
        encoding="utf-8"
    )

    assert "proof_graph" in graph_doc
    assert "dependency_graph" not in graph_doc
    assert "comp.views.receipt_graph" in graph_doc
    assert "MySQLArtifactStore is an ArtifactStore implementation" in graph_doc


def test_receipt_graph_renderers_have_non_authority_module_boundary():
    from comp.views import receipt_graph

    assert "render-only" in (receipt_graph.__doc__ or "").lower()
    assert "export_receipt_proof_graph" not in receipt_graph.__dict__
    assert "replay_public_projection" not in receipt_graph.__dict__
    assert "project_public_row" not in receipt_graph.__dict__


def test_pyproject_packages_comp_core_scenarios_and_agent_layer():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    from comp.persistence import (
        ArtifactStore,
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
        "comp.explanation",
        "comp.judgment",
        "comp.persistence",
        "comp.scenarios",
        "comp.scenarios.synthetic",
        "comp.views",
        "minchoagnt",
    ]
    assert pyproject["tool"]["setuptools"]["package-data"] == {
        "comp.scenarios.synthetic": ["profiles/*.yaml"],
    }
    assert "py-modules" not in setuptools_config

    scripts = pyproject["project"].get("scripts", {})
    assert scripts["minchoagnt"] == "minchoagnt.cli:main"
    assert scripts["comp-receipt-graph"] == "comp.explanation.receipt_graph_cli:main"

    dependencies = pyproject["project"].get("dependencies", [])
    assert not any(dependency.startswith("lark") for dependency in dependencies)

    from comp.explanation import ReceiptProofGraph, export_receipt_proof_graph

    assert ReceiptProofGraph is not None
    assert export_receipt_proof_graph is not None
    assert ArtifactStore is not None
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
