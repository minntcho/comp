from pathlib import Path
import tomllib

import comp
from comp import (
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    DependencyFingerprint,
    Fact,
    FixpointEngine,
    JudgmentState,
    PublicOutput,
    PublicOutputBlocked,
    PublicOutputReceipt,
    PublicOutputReceiptCitations,
    PublicOutputSpec,
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

DOC_HEADER_FIELDS = (
    "Status",
    "Owner",
    "Last checked against code",
    "Can block PRs",
)
DOC_STATUS_BLOCKING = {
    "active-contract": "yes",
    "implementation-map": "limited",
    "north-star": "limited",
    "historical-note": "no",
}
DOC_OWNERS = {
    "agent-layer",
    "docs",
    "explanation",
    "persistence",
    "retrieval",
    "scenario-lab",
    "trust-kernel",
}
COMPILER_TOOL_STABLE_PUBLIC = {
    "CompilerTool",
    "ValidationReport",
    "resolver_tasks_from_report",
    "prepare_commit",
    "build_public_output_receipt",
    "compile_report_to_facts",
}
COMPILER_TOOL_ADVANCED_PUBLIC = {
    "SemanticJudgment",
    "ReferenceOption",
    "CanonicalReference",
    "CalculationTrace",
    "CalculatedClaim",
    "ReviewPackage",
    "ReviewDecision",
    "ReferenceCatalog",
    "ReferenceResolver",
}
COMPILER_TOOL_EXPERIMENTAL_NOT_QUICKSTART = {
    "active_retrieval_query_policies",
    "profile_declaration_fingerprint",
    "domain_pack_declaration_fingerprint",
    "rule_family_declaration_fingerprint",
    "semantic_rubric_declaration_fingerprint",
    "reference_query_for_obligation_from_policy",
    "reference_query_for_obligation_from_profile_policy",
    "reference_query_for_obligation_from_policies",
    "reference_query_for_obligation_from_resolver_tasks",
    "reference_query_from_resolver_task",
    "select_reference_binding",
    "apply_reference_selection",
    "retry_blocked_calculation",
    "apply_calculation_result",
    "add_compile_report_facts",
    "add_commit_preparation_facts",
    "with_recomputed_status",
    "recompute_report_status",
}


def _governed_architecture_docs():
    return sorted(Path("docs/architecture").glob("*.md")) + sorted(
        Path("docs/archive/architecture").glob("*.md")
    )


def _doc_header(path):
    header = {}
    for line in path.read_text(encoding="utf-8").splitlines()[:8]:
        if ": " in line:
            key, value = line.split(": ", 1)
            header[key] = value
    return header


def _docs_relative_path(path):
    return path.relative_to("docs").as_posix()


def _readme_compiler_tool_quickstart():
    readme = Path("README.md").read_text(encoding="utf-8")
    for block in readme.split("```python")[1:]:
        code = block.split("```", 1)[0]
        if "from comp.compiler_tool import" in code:
            return code
    raise AssertionError("README does not include a compiler_tool quickstart block.")


def test_top_level_package_exposes_active_judgment_surface():
    assert Fact is not None
    assert JudgmentState is not None
    assert SubjectRef is not None
    assert FixpointEngine is not None
    assert SelectionReceipt is not None
    assert PublicOutputReceipt is not None
    assert PublicOutputReceiptCitations is not None
    assert PublicOutputSpec is not None
    assert PublicOutputBlocked is not None
    assert PublicOutput is not None
    assert PublicOutputReceipt is PublicOutputReceipt
    assert PublicOutputReceiptCitations is PublicOutputReceiptCitations
    assert PublicOutputReceipt is not None
    assert PublicOutputReceiptCitations is not None
    assert DependencyFingerprint is not None


def test_top_level_package_no_longer_exports_legacy_runner_surface():
    assert not hasattr(comp, "ESGPipelineRunner")
    assert not hasattr(comp, "CompiledESGPipelineRunner")
    assert not hasattr(comp, "PipelineResources")
    assert not hasattr(comp, "PipelineRunResult")


def test_compiler_tool_stable_public_surface_is_exported_and_in_readme():
    import comp.compiler_tool as compiler_tool

    quickstart = _readme_compiler_tool_quickstart()

    for name in COMPILER_TOOL_STABLE_PUBLIC:
        assert hasattr(compiler_tool, name), name
        assert name in quickstart, name


def test_compiler_tool_advanced_surface_is_documented():
    import comp.compiler_tool as compiler_tool

    api_doc = Path("docs/api/compiler-tool.md").read_text(encoding="utf-8")
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    assert "## API References" in docs_index
    assert "api/compiler-tool.md" in docs_index
    assert "Advanced public API" in api_doc
    for name in COMPILER_TOOL_ADVANCED_PUBLIC:
        assert hasattr(compiler_tool, name), name
        assert name in api_doc, name
    assert "__all__ is an import-convenience surface" in api_doc
    assert "__all__ is not the stability contract" in api_doc


def test_compiler_tool_experimental_surface_is_not_in_readme_quickstart():
    quickstart = _readme_compiler_tool_quickstart()
    api_doc = Path("docs/api/compiler-tool.md").read_text(encoding="utf-8")

    assert "Experimental / internal-ish API" in api_doc
    for name in COMPILER_TOOL_EXPERIMENTAL_NOT_QUICKSTART:
        assert name in api_doc, name
        assert name not in quickstart, name


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
    assert "PublicOutputValueCommitment" in hardening
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
    assert "ReferenceOption / CanonicalReference" in working_theory
    assert "ReviewPackage / ReviewDecision / PublicOutputReceipt" in working_theory
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


def test_document_governance_defines_authority_lifecycle_locations():
    governance = Path(
        "docs/architecture/document-governance.md"
    ).read_text(encoding="utf-8")
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    assert "Document headers are the metadata source of truth." in governance
    assert "`docs/index.md` is the navigation source of truth." in governance
    assert "docs/architecture/ root is an entry surface" in governance
    assert "demotion changes both status and location" in governance

    for lifecycle_rule in (
        "active-contract -> docs/architecture/contracts/",
        "implementation-map -> docs/architecture/maps/",
        "north-star -> docs/architecture/north-stars/",
        "historical-note -> docs/archive/architecture/",
        "implementation plan -> docs/archive/plans/",
        "migration history -> docs/archive/migration/",
    ):
        assert lifecycle_rule in governance

    assert "The document header is the metadata source of truth" in docs_index
    assert "this index is the navigation source of truth" in docs_index


def test_document_governance_documents_smoke_enforcement():
    governance = Path(
        "docs/architecture/document-governance.md"
    ).read_text(encoding="utf-8")

    assert "## Smoke Enforcement" in governance
    assert "required header keys" in governance
    assert "status-to-blocking match" in governance
    assert "lifecycle location" in governance
    assert "index listing" in governance


def test_governed_architecture_docs_have_valid_machine_readable_headers():
    for path in _governed_architecture_docs():
        header = _doc_header(path)

        assert set(DOC_HEADER_FIELDS).issubset(header), path
        assert header["Status"] in DOC_STATUS_BLOCKING, path
        assert header["Owner"] in DOC_OWNERS, path
        assert header["Can block PRs"] == DOC_STATUS_BLOCKING[header["Status"]], path
        assert len(header["Last checked against code"].split("-")) == 3, path


def test_governed_architecture_docs_match_index_and_lifecycle_location():
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")
    governed_docs = _governed_architecture_docs()

    for path in governed_docs:
        header = _doc_header(path)
        rel_path = _docs_relative_path(path)

        assert rel_path in docs_index, path
        if header["Status"] == "historical-note":
            assert path.match("docs/archive/architecture/*.md"), path
        else:
            assert path.match("docs/architecture/*.md"), path

    assert not [
        path
        for path in Path("docs/architecture").rglob("*.md")
        if "REQUIRED SUB-SKILL:" in path.read_text(encoding="utf-8")
    ]
    assert not Path("docs/superpowers/plans").exists()


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
            "2026-05-22",
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
            "active-contract",
            "trust-kernel",
            "yes",
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
        "scenario-trust-runtime-bridge.md": (
            "north-star",
            "scenario-lab",
            "limited",
            "2026-05-22",
        ),
        "trust-kernel-extension-rings.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-22",
        ),
        "trust-kernel-hardening.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-21",
        ),
    }

    architecture_docs = sorted(Path("docs/architecture").glob("*.md")) + sorted(
        Path("docs/archive/architecture").glob("*.md")
    )
    assert {path.name for path in architecture_docs} == set(expected_status)

    for path in architecture_docs:
        status, owner, blocking, checked_date = expected_status[path.name]
        text = path.read_text(encoding="utf-8")
        assert f"Status: {status}" in text
        assert f"Owner: {owner}" in text
        assert f"Last checked against code: {checked_date}" in text
        assert f"Can block PRs: {blocking}" in text


def test_historical_notes_and_plans_live_in_archive_locations():
    root_architecture_docs = sorted(Path("docs/architecture").glob("*.md"))
    archived_architecture_docs = sorted(Path("docs/archive/architecture").glob("*.md"))
    archived_plan_docs = sorted(Path("docs/archive/plans").glob("*.md"))

    assert not Path("docs/superpowers/plans").exists()
    assert {path.name for path in archived_architecture_docs} == {
        "active-surface-cutover.md",
        "legacy-archive-cutover-plan.md",
        "llm-orchestrated-compiler-tool-loop.md",
    }
    assert {path.name for path in archived_plan_docs} == {
        "2026-05-20-trust-kernel-hardening.md",
        "2026-05-21-production-trust-spine-db-v1.md",
        "2026-05-21-raw-claim-promotion-boundary.md",
        "2026-05-22-receipt-proof-graph-boundary-prework.md",
    }

    assert not [
        path
        for path in root_architecture_docs
        if "Status: historical-note" in path.read_text(encoding="utf-8")
    ]
    for path in archived_architecture_docs:
        text = path.read_text(encoding="utf-8")
        assert "Status: historical-note" in text
        assert "Can block PRs: no" in text


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
    assert "archive/architecture/active-surface-cutover.md" in docs_index
    assert "architecture/friendly-authority-vocabulary.md" in docs_index
    assert "archive/architecture/legacy-archive-cutover-plan.md" in docs_index
    assert "archive/architecture/llm-orchestrated-compiler-tool-loop.md" in docs_index
    assert "architecture/production-trust-spine-database.md" in docs_index
    assert "architecture/scenario-trust-runtime-bridge.md" in docs_index
    assert "docs/archive/plans/" in docs_index
    assert "examples/scenario_pack_repo/README.md" in docs_index


def test_downstream_scenario_pack_skeleton_documents_ci_contract():
    readme = Path("docs/examples/scenario_pack_repo/README.md").read_text(
        encoding="utf-8"
    )
    pyproject = Path("docs/examples/scenario_pack_repo/pyproject.toml").read_text(
        encoding="utf-8"
    )
    workflow = Path(
        "docs/examples/scenario_pack_repo/.github/workflows/scenario-contracts.yml"
    ).read_text(encoding="utf-8")
    extensions = Path("docs/extensions/scenario-packs.md").read_text(
        encoding="utf-8"
    )

    assert "comp-scenario-packs" in readme
    assert "comp scenario init packs/public_projection_smoke" in readme
    assert "comp scenario init --force packs/public_projection_smoke" in readme
    assert "comp scenario run packs/public_projection_smoke/scenario.json" in readme
    assert "Do not import `tests.*`" in readme
    assert "comp @ git+https://github.com/minntcho/comp@main" in pyproject
    assert "python -m pip install -e ." in workflow
    assert "comp scenario run packs/public_projection_smoke/scenario.json" in workflow
    assert "examples/scenario_pack_repo/README.md" in extensions


def test_scenario_trust_runtime_bridge_keeps_public_runner_narrow():
    bridge = Path("docs/architecture/scenario-trust-runtime-bridge.md").read_text(
        encoding="utf-8"
    )

    assert "Status: north-star" in bridge
    assert "External packs prepare canonical or candidate trust inputs." in bridge
    assert "Product ingestion stays outside comp." in bridge
    assert "TrustRuntime" in bridge
    assert "input_mode: canonical_bundle" in bridge
    assert "comp scenario run" in bridge
    assert "tests.domain_scenarios" in bridge
    assert "Does the change keep raw product ingestion outside comp?" in bridge


def test_friendly_authority_vocabulary_names_rename_path_without_moving_authority():
    vocabulary = Path(
        "docs/architecture/friendly-authority-vocabulary.md"
    ).read_text(encoding="utf-8")

    assert "Status: active-contract" in vocabulary
    assert "repo exposes only the canonical authority names" in vocabulary
    assert "`ClaimCandidate` | 검증 전 입력값" in vocabulary
    assert "`EvidenceRef` | 근거자료 위치" in vocabulary
    assert "`ValidationRequirement` | 보완 필요 항목" in vocabulary
    assert "`CanonicalReference` | 확정 기준" in vocabulary
    assert "`PublicOutputReceipt` | 공개 승인 증표" in vocabulary
    assert "`ArtifactEnvelope` | 감사 산출물 기록" in vocabulary
    assert "Active package surfaces must use the canonical names above." in vocabulary
    assert "tests/test_complete_friendly_rename.py" in vocabulary
    assert "Historical snapshots under" in vocabulary
    assert "The first implementation lives in `comp.schema_labels`" in vocabulary
    assert "schema_label_ko(\"ClaimCandidate\")" in vocabulary
    assert "The first helper lives in `comp.user_messages`" in vocabulary
    assert "user_message_for_reason(\"unsupported_unit\")" in vocabulary
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
    assert "build_public_output" not in receipt_graph.__dict__


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
        "comp.cli",
        "comp.compiler_tool",
        "comp.explanation",
        "comp.judgment",
        "comp.persistence",
        "comp.runtime",
        "comp.scenario_contracts",
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
    assert scripts["comp"] == "comp.cli.scenario:main"
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
    assert not Path("legacy").exists()
    assert "comp.runner" not in (comp.__doc__ or "")


def test_comp_core_does_not_import_agent_layer():
    comp_sources = Path("comp").rglob("*.py")
    assert not [
        path
        for path in comp_sources
        if "minchoagnt" in path.read_text(encoding="utf-8")
    ]
