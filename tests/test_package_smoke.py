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
    "InterpretationHypothesis",
    "ClaimCandidate",
    "EvidenceRef",
    "CompilerTool",
    "ValidationReport",
    "resolver_tasks_from_report",
    "prepare_commit",
    "build_public_output_receipt",
    "compile_report_to_facts",
}
COMPILER_TOOL_QUICKSTART_PATH = {
    "InterpretationHypothesis",
    "ClaimCandidate",
    "EvidenceRef",
    "CompilerTool",
    "prepare_commit",
}
TOP_LEVEL_QUICKSTART_GATE = {
    "PublicOutputBlocked",
    "PublicOutputSpec",
    "build_public_output",
}
PUBLIC_OUTPUT_GATE_PUBLIC = {
    "PublicOutput",
    "PublicOutputBlocked",
    "PublicOutputSpec",
    "PublicOutputReceipt",
    "PublicOutputReceiptCitations",
    "PublicOutputValueCommitment",
    "DependencyFingerprint",
    "build_public_output",
}
SCENARIO_CONTRACTS_STABLE_PUBLIC = {
    "InvariantResult",
    "ScenarioManifest",
    "ScenarioManifestError",
    "RuntimeCase",
    "RuntimeProjection",
    "ScenarioBundleExistsError",
    "ScenarioResult",
    "load_manifest",
    "load_runtime_case",
    "runtime_case_from_mapping",
    "runtime_case_to_mapping",
    "runtime_projection_to_mapping",
    "write_runtime_case",
    "load_artifact_envelopes",
    "write_artifact_envelopes",
    "artifact_envelope_from_mapping",
    "artifact_envelope_to_mapping",
    "run_scenario",
    "write_public_projection_smoke_bundle",
    "write_report",
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
COMPILER_TOOL_BEHAVIOR_DECLARATION_PUBLIC = {
    "DomainPack",
    "CompilerProfile",
    "RuleFamily",
    "SemanticRubric",
    "JudgePolicy",
    "ReferenceCatalog",
    "ReferenceCatalogSnapshot",
    "ReferenceRecord",
    "CalculationFormula",
    "RetrievalQueryPolicy",
    "RetrievalQueryRule",
}
COMPILER_TOOL_EXPERIMENTAL_NOT_QUICKSTART = {
    "active_retrieval_query_policies",
    "profile_declaration_fingerprint",
    "domain_pack_declaration_fingerprint",
    "rule_family_declaration_fingerprint",
    "semantic_rubric_declaration_fingerprint",
    "reference_query_for_requirement_from_policy",
    "reference_query_for_requirement_from_profile_policy",
    "reference_query_for_requirement_from_policies",
    "reference_query_for_requirement_from_resolver_tasks",
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
    governed_dirs = (
        Path("docs/architecture"),
        Path("docs/architecture/contracts"),
        Path("docs/architecture/maps"),
        Path("docs/architecture/north-stars"),
        Path("docs/archive/architecture"),
    )
    return sorted(path for directory in governed_dirs for path in directory.glob("*.md"))


def _matches_lifecycle_location(path, status):
    if status == "active-contract":
        return path == Path("docs/architecture/document-governance.md") or path.match(
            "docs/architecture/contracts/*.md"
        )
    if status == "implementation-map":
        return path.match("docs/architecture/maps/*.md")
    if status == "north-star":
        return path.match("docs/architecture/north-stars/*.md")
    if status == "historical-note":
        return path.match("docs/archive/architecture/*.md")
    raise AssertionError(f"Unknown architecture doc status: {status}")


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
    start = "<!-- compiler-tool-quickstart:start -->"
    end = "<!-- compiler-tool-quickstart:end -->"
    if start not in readme or end not in readme:
        raise AssertionError("README does not mark the compiler_tool quickstart.")
    quickstart_section = readme.split(start, 1)[1].split(end, 1)[0]
    for block in quickstart_section.split("```python")[1:]:
        code = block.split("```", 1)[0]
        if "from comp.compiler_tool import" in code:
            return code
    raise AssertionError("README quickstart marker does not include a python block.")


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


def test_compiler_tool_stable_public_surface_is_exported_and_documented():
    import comp.compiler_tool as compiler_tool

    api_doc = Path("docs/api/compiler-tool.md").read_text(encoding="utf-8")

    for name in COMPILER_TOOL_STABLE_PUBLIC:
        assert hasattr(compiler_tool, name), name
        assert name in api_doc, name


def test_readme_compiler_tool_quickstart_uses_required_public_path():
    quickstart = _readme_compiler_tool_quickstart()

    for name in COMPILER_TOOL_QUICKSTART_PATH:
        assert name in quickstart, name
    for name in TOP_LEVEL_QUICKSTART_GATE:
        assert name in quickstart, name


def test_readme_compiler_tool_quickstart_executes_receipt_gate_path():
    namespace = {}
    exec(_readme_compiler_tool_quickstart(), namespace)

    assert namespace["blocked_without_receipt"] is True
    assert namespace["row"] == {"amount": 1200, "unit": "kWh"}
    assert "internal_note" not in namespace["row"]


def test_public_output_gate_api_reference_is_documented():
    api_doc = Path("docs/api/public-output-gate.md").read_text(encoding="utf-8")
    compiler_tool_doc = Path("docs/api/compiler-tool.md").read_text(
        encoding="utf-8"
    )
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    assert "api/public-output-gate.md" in docs_index
    assert "api/public-output-gate.md" in compiler_tool_doc
    assert "PublicOutputReceipt is the projection authority" in api_doc
    assert "ValidationReport is not public-output authority" in api_doc
    assert "build_public_output(..., receipt=...)" in api_doc
    assert "materialized view, not authority" in api_doc
    for name in PUBLIC_OUTPUT_GATE_PUBLIC:
        assert hasattr(comp, name), name
        assert name in api_doc, name


def test_scenario_contracts_api_reference_is_documented():
    import comp.scenario_contracts as scenario_contracts
    from comp.persistence import ArtifactEnvelope

    api_doc = Path("docs/api/scenario-contracts.md").read_text(encoding="utf-8")
    docs_index = Path("docs/index.md").read_text(encoding="utf-8")

    assert "api/scenario-contracts.md" in docs_index
    assert "Public scenario bridge contracts" in api_doc
    assert "input_mode='canonical_bundle'" in api_doc
    assert "prepared RuntimeCase + ArtifactEnvelope bundle" in api_doc
    assert "Product ingestion stays outside comp." in api_doc
    assert "ArtifactEnvelope is a public companion surface" in api_doc
    assert "comp.scenario_contracts.__all__ is the stability contract" in api_doc
    for name in SCENARIO_CONTRACTS_STABLE_PUBLIC:
        assert hasattr(scenario_contracts, name), name
        assert name in api_doc, name
    assert ArtifactEnvelope is not None
    assert "write_public_projection_smoke_bundle" in api_doc


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


def test_compiler_tool_behavior_declaration_surface_is_documented():
    import comp.compiler_tool as compiler_tool

    api_doc = Path("docs/api/compiler-tool.md").read_text(encoding="utf-8")

    assert "## Behavior declaration surfaces" in api_doc
    assert "They are not authority overrides." in api_doc
    assert "DomainPack is a declaration library." in api_doc
    assert "CompilerProfile is the active behavior lock." in api_doc
    assert "Neither is authority." in api_doc
    for name in COMPILER_TOOL_BEHAVIOR_DECLARATION_PUBLIC:
        assert hasattr(compiler_tool, name), name
        assert name in api_doc, name


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


def test_readme_tracks_policy_boundary_vocabulary_surface():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "comp.policy" in readme
    assert "pre-validation policy boundary vocabulary" in readme
    assert "MaterialDescriptor" in readme
    assert "PolicyEffect" in readme
    assert "ConflictResolver" in readme
    assert "PolicyAssembly" in readme
    assert "PolicyAssemblySubject" in readme
    assert "ScopedGrant" in readme
    assert "SelectionDecision" in readme
    assert "DecisionLedger" in readme
    assert "SelectedValidationContract" in readme
    assert "ShadowPolicyComparison" in readme
    assert "policy_artifact_digest" in readme
    assert "PolicyAssembly` can assemble a `DecisionLedger` and matching" in readme
    assert "Pipeline scope changes are represented only by `grant_scope`" in readme
    assert "`restrict_scope` `PolicyEffect`s" in readme
    assert "actual and counterfactual policy outputs" in readme
    assert "selected, held, rejected, and projection-candidate deltas" in readme
    assert "provide stable audit identifiers only" in readme
    assert "pre-validation and non-authoritative" in readme
    assert "validation" in readme
    assert "receipt authority" in readme
    assert "replay authority가 아니다" in readme


def test_readme_tracks_validation_handoff_runtime_bridge():
    readme = Path("README.md").read_text(encoding="utf-8")

    assert "comp.runtime.ValidationHandoff" in readme
    assert "selected validation contract를" in readme
    assert "`InterpretationHypothesis`로 옮기는 얇은 runtime bridge" in readme
    assert "decision target snapshot" in readme
    assert "claim field" in readme
    assert "compile, commit, receipt, or replay authority" in readme
    assert "ValidationHandoffClaim" in readme


def test_readme_routes_new_work_through_current_architecture_entrypoints():
    readme = Path("README.md").read_text(encoding="utf-8")

    for entrypoint in (
        "docs/index.md",
        "docs/architecture/document-governance.md",
        "docs/architecture/contracts/policy-boundary.md",
        "docs/architecture/maps/policy-assembled-trust-kernel.md",
    ):
        assert entrypoint in readme

    assert readme.index("docs/index.md") < readme.index(
        "docs/architecture/document-governance.md"
    )
    assert readme.index(
        "docs/architecture/contracts/policy-boundary.md"
    ) < readme.index("docs/architecture/maps/policy-assembled-trust-kernel.md")

    for guardrail in (
        "작업 시작 전에 이 순서로 현재 authority를 확인한다.",
        "policy-boundary",
        "policy-assembled-trust-kernel",
        "새 policy work는 `comp.policy`처럼 작은 pre-validation vocabulary "
        "slice에서 시작한다.",
        "archive 문서는 current guidance가 아니다.",
    ):
        assert guardrail in readme


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
    hardening = Path(
        "docs/architecture/contracts/trust-kernel-hardening.md"
    ).read_text(encoding="utf-8")

    assert "## Projection Numeric Value Policy" in hardening
    assert "PublicOutputValueCommitment" in hardening
    assert "Decimal" in hardening


def test_trust_kernel_hardening_documents_profile_baseline_policy():
    hardening = Path(
        "docs/architecture/contracts/trust-kernel-hardening.md"
    ).read_text(encoding="utf-8")

    assert "profile-declared baseline" in hardening
    assert "known fields and allowed units" in hardening
    assert "run_profile_rules" in hardening


def test_working_theory_status_section_tracks_current_rebuild_state():
    working_theory = Path(
        "docs/architecture/maps/obligation-kernel-working-theory.md"
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
        "docs/architecture/maps/domain-scenario-pack-generation.md"
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
        "docs/architecture/contracts/compiler-domain-boundary.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/contracts/trust-kernel-extension-rings.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/contracts/persistence-ledger-boundary.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/contracts/artifact-envelope-builder.md": (
            "Status: active-contract",
            "Can block PRs: yes",
        ),
        "docs/architecture/north-stars/retrieval-fabric-north-star.md": (
            "Status: north-star",
            "Can block PRs: limited",
        ),
        "docs/architecture/maps/obligation-kernel-working-theory.md": (
            "Status: implementation-map",
            "Can block PRs: limited",
        ),
        "docs/architecture/maps/domain-scenario-pack-generation.md": (
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


def test_policy_boundary_contract_keeps_policy_non_authoritative():
    policy_boundary = Path(
        "docs/architecture/contracts/policy-boundary.md"
    ).read_text(encoding="utf-8")
    selection_tiers = Path(
        "docs/profile-schema-selection-resolution-tiers.md"
    ).read_text(encoding="utf-8")

    for line in (
        "Policy may shape validation input. Policy may not validate.",
        "It does not govern compiler validation, receipt authority, or replay authority.",
        "A `ScopedGrant` is pipeline access, not trust authority.",
        "`projection_candidate` means pre-authority eligibility for later receipt",
        "PublicOutputReceipt",
        "Kernel invariants are non-overridable.",
        "No policy output validates a claim.",
        "No scoped grant authorizes public projection.",
        "No embedding or LLM output enters validation_handoff without selection basis.",
        "ScopedGrant is not PublicOutputReceipt.",
        "Capabilities may recommend. Policies may issue scoped access.",
        "Not every term in this document is currently a public Python API.",
        "The first implementation slices live in `comp.policy`.",
        "`MaterialDescriptor`, `PolicyEffect`, `ConflictResolver`, `PolicyAssembly`,",
        "`PolicyAssembly` groups descriptors, effects, assembly subjects, and resolver",
        "`PolicyAssembly` may also build a matching `SelectedValidationContract`",
        "`PolicyAssembly` may assemble a `DecisionLedger` and matching",
        "`ShadowPolicyComparison` compares actual and counterfactual policy outputs",
        "`ShadowPolicyComparison` may compare actual and counterfactual",
        "policy outputs, but it is audit material only. `policy_artifact_digest(...)`,",
        "`DecisionLedger.digest()`, `SelectedValidationContract.digest()`, and",
        "`ShadowPolicyComparison.digest()` expose stable audit identifiers",
        "Policy artifact digest is not PublicOutputReceipt.",
        "Pipeline scope may appear",
        "only on `grant_scope` and `restrict_scope` effects",
        "`PolicyEffect.scope` is valid only on `grant_scope` and `restrict_scope`.",
        "Selection status is not pipeline access",
        "Status effects must not carry pipeline scope.",
        "selected decision target snapshots",
        "handoff claim field must match that target",
        "`SelectedValidationContract` as compiler-facing input shape, not validation",
        "target snapshots match",
        "`comp.runtime.ValidationHandoff` bridges selected validation",
    ):
        assert line in policy_boundary

    assert "docs/architecture/contracts/policy-boundary.md" in selection_tiers
    assert "selection strategies must obey" in selection_tiers


def test_policy_assembled_trust_kernel_map_tracks_growth_shape():
    policy_map = Path(
        "docs/architecture/maps/policy-assembled-trust-kernel.md"
    ).read_text(encoding="utf-8")

    for line in (
        "Status: implementation-map",
        "The active authority contract remains",
        "policy-boundary.md",
        "The process kernel is fixed.",
        "Policy assemblies are profile-specific.",
        "Capability activation is artifact-conditioned.",
        "Authority boundaries are invariant.",
        "`SelectedValidationContract` freezes what the compiler is allowed to see",
        "selected decision target snapshot",
        "bind each handoff claim field to the frozen target",
        "selected for validation != selected for projection",
        "`ScopedGrant` is pipeline access, not trust authority.",
        "Status and evidence effects are unscoped",
        "pipeline scope",
        "grant_scope and restrict_scope effects",
        "Composition step from effects to decisions and scoped grants.",
        "Ledger and selected-contract assembly step from descriptors, effects, and",
        "and selected-contract assembly, scoped pipeline access, selection status,",
        "`DecisionLedger` is the audit spine for policy assembly.",
        "PublicOutputReceipt",
        "Runtime bridge from selected contract to compiler input.",
        "Actual-vs-counterfactual audit comparison.",
        "`comp.runtime.ValidationHandoff` is the first bridge",
        "`CompilerTool`, commit, receipt, projection, or replay authority.",
        "policy artifact digest",
        "comp.policy.ShadowPolicyComparison",
        "comp.policy.policy_artifact_digest",
        "The first implemented part is",
        "ShadowPolicyComparison, which records decision deltas without replaying",
        "stable policy artifact digests",
        "actual-vs-counterfactual policy deltas",
        "Future policy work should connect to that direction instead of introducing a",
        "parallel source of selection truth, validation truth, receipt truth, or",
        "projection truth.",
        "This map does not prescribe:",
        "`comp.policy.MaterialDescriptor`, `PolicyEffect`, `ConflictResolver`,",
        "`PolicyAssembly`, `ScopedGrant`, `SelectionDecision`, `DecisionLedger`,",
        "`SelectedValidationContract`, and `ShadowPolicyComparison` are the first",
    ):
        assert line in policy_map


def test_product_facade_observation_map_defines_lab_without_contracting_lifecycle():
    product_map = Path(
        "docs/architecture/maps/product-facade-observation.md"
    ).read_text(encoding="utf-8")
    readme = Path("README.md").read_text(encoding="utf-8")

    for line in (
        "Status: implementation-map",
        "This map is observational, not prescriptive.",
        "not an artifact lifecycle contract",
        "comp.runtime is not production runtime",
        "reference/conformance runtime surface",
        "outside the `comp` package",
        "first facade must be comp-backed",
        "ceremony measurement, not independent authority reimplementation",
        "submit(input)",
        "publish(run_id)",
        "audit(public_row_id)",
        "canonical_fast_path",
        "policy_preflight_path",
        "artifact touch log",
        "This shape is illustrative.",
        "not a stable artifact registry or passport schema",
        "no artifact registry yet",
        "no Artifact Passport schema yet",
        "no comp.contracts extraction yet",
        "no native production authority engine yet",
        "Fast path may skip policy preflight",
        "must never skip compiler validation",
        "receipt-gated projection",
        "replay requirements when those states are claimed",
        "Promotion to Artifact Lifecycle Boundary requires",
    ):
        assert line in product_map

    assert "product-facade-observation.md" in readme
    assert "does not make `comp.runtime` a production runtime" in readme


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
        assert _matches_lifecycle_location(path, header["Status"]), path

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
            "2026-05-22",
        ),
        "document-governance.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-22",
        ),
        "compiler-domain-boundary.md": (
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
        "internal-execution-design-map.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-23",
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
            "2026-05-22",
        ),
        "obligation-kernel-working-theory.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-20",
        ),
        "policy-assembled-trust-kernel.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-26",
        ),
        "product-facade-observation.md": (
            "implementation-map",
            "trust-kernel",
            "limited",
            "2026-05-26",
        ),
        "persistence-ledger-boundary.md": (
            "active-contract",
            "persistence",
            "yes",
            "2026-05-22",
        ),
        "policy-boundary.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-26",
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
            "2026-05-22",
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
            "2026-05-26",
        ),
        "trust-kernel-hardening.md": (
            "active-contract",
            "trust-kernel",
            "yes",
            "2026-05-21",
        ),
    }

    architecture_docs = _governed_architecture_docs()
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
    body_architecture_docs = [
        path
        for directory in (
            Path("docs/architecture/contracts"),
            Path("docs/architecture/maps"),
            Path("docs/architecture/north-stars"),
        )
        for path in directory.glob("*.md")
    ]
    archived_architecture_docs = sorted(Path("docs/archive/architecture").glob("*.md"))
    archived_plan_docs = sorted(Path("docs/archive/plans").glob("*.md"))

    assert not Path("docs/superpowers/plans").exists()
    assert {path.name for path in root_architecture_docs} == {
        "document-governance.md",
    }
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
        for path in root_architecture_docs + body_architecture_docs
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
    assert "architecture/contracts/compiler-domain-boundary.md" in docs_index
    assert "architecture/contracts/policy-boundary.md" in docs_index
    assert "architecture/maps/policy-assembled-trust-kernel.md" in docs_index
    assert "architecture/maps/product-facade-observation.md" in docs_index
    assert "architecture/contracts/friendly-authority-vocabulary.md" in docs_index
    assert "archive/architecture/legacy-archive-cutover-plan.md" in docs_index
    assert "archive/architecture/llm-orchestrated-compiler-tool-loop.md" in docs_index
    assert "architecture/north-stars/production-trust-spine-database.md" in docs_index
    assert "architecture/north-stars/scenario-trust-runtime-bridge.md" in docs_index
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
    bridge = Path(
        "docs/architecture/north-stars/scenario-trust-runtime-bridge.md"
    ).read_text(encoding="utf-8")

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
        "docs/architecture/contracts/friendly-authority-vocabulary.md"
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
    assert "## 6. Residual Field Vocabulary Audit" in vocabulary
    assert "active `ValidationReport` field names are" in vocabulary
    assert "complete. Active Python-facing report fields" in vocabulary
    assert "`ValidationReport.evidence_refs` | Grounding references" in vocabulary
    assert "`ValidationReport.reference_options` | Candidate-only" in vocabulary
    assert "`ValidationReport.canonical_references` | Deterministically" in vocabulary
    assert "`ValidationReport.calculated_claims` | Calculated values" in vocabulary
    assert "`ValidationReport.validation_requirements` | Open work" in vocabulary
    assert "`ValidationReport.resolved_validation_requirements` | Completed" in vocabulary
    assert "Do not add compatibility" in vocabulary
    assert "aliases for the previous field names" in vocabulary
    assert "Codec-bound receipt and replay vocabulary" in vocabulary
    assert "`PublicOutputReceipt.projection_id`" in vocabulary
    assert "`DependencyFingerprint.dependency_kind=\"evidence_witness\"`" in vocabulary
    assert "Do not add a blanket ban on `projection` or `witness`" in vocabulary
    assert "### Residual obligation vocabulary" in vocabulary
    assert "`ReviewPackage.open_obligation_ids`" in vocabulary
    assert "`PublicOutputReceiptCitations.resolved_obligation_ids`" in vocabulary
    assert "`SyntheticResolutionArtifact.obligation_id`" in vocabulary
    assert "`ExpectedReceipt.resolved_obligation_ids`" in vocabulary
    assert "Do not rename all remaining `obligation` strings in one PR." in vocabulary
    assert "Receipt schema and governance facts" in vocabulary
    assert "Synthetic resolution artifact payloads" in vocabulary
    assert "Docs prose and historical theory language" in vocabulary
    assert "Test-local wording" in vocabulary
    assert "Only a clean public-output receipt can authorize public output." in vocabulary


def test_production_database_north_star_is_provisional_and_discoverable():
    db_north_star = Path(
        "docs/architecture/north-stars/production-trust-spine-database.md"
    ).read_text(encoding="utf-8")
    persistence_boundary = Path(
        "docs/architecture/contracts/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "Status: north-star" in db_north_star
    assert "not a final database schema" in db_north_star
    assert "intentionally provisional" in db_north_star
    assert "Expected to evolve" in db_north_star
    assert "production-trust-spine-database.md" in persistence_boundary


def test_production_database_north_star_tracks_v1_mysql_spine():
    db_doc = Path(
        "docs/architecture/north-stars/production-trust-spine-database.md"
    ).read_text(encoding="utf-8")
    persistence_doc = Path(
        "docs/architecture/contracts/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "## 12. Current Implementation Status" in db_doc
    assert "MySQLArtifactStore" in db_doc
    assert "MySQLReceiptLedger" in db_doc
    assert "ledger_receipt_artifact_refs" in db_doc
    assert "MySQL trust spine" in persistence_doc


def test_persistence_ledger_boundary_documents_mysql_operating_contract():
    persistence_doc = Path(
        "docs/architecture/contracts/persistence-ledger-boundary.md"
    ).read_text(encoding="utf-8")

    assert "## 14. MySQL Operating Contract" in persistence_doc
    for line in (
        "MySQL stores replay inputs and receipt records.",
        "MySQL does not authorize public projection.",
        "Any materialized or indexed table is receipt-derived and must be replay-verifiable.",
        "ArtifactEnvelope writes are idempotent for the same artifact_id, artifact_kind, schema_version, and body_digest.",
        "The same artifact_id with a different kind, schema_version, or body_digest raises ArtifactConflict.",
        "ReceiptLedgerKey conflicts raise ReceiptConflict.",
        "MySQLArtifactStore.record(...) commits artifact-envelope writes independently.",
        "MySQLReceiptLedger.record(...) inserts the receipt body and receipt-derived indexes in one transaction before commit.",
        "apply_trust_spine_schema(...) is idempotent DDL setup, not an online migration runner.",
        "A recorded receipt without replayable artifacts is storage state only; projection stays blocked until replay_public_projection(...) succeeds.",
    ):
        assert line in persistence_doc


def test_artifact_envelope_builder_contract_separates_coverage_from_materialization():
    builder_doc = Path(
        "docs/architecture/contracts/artifact-envelope-builder.md"
    ).read_text(encoding="utf-8")

    for line in (
        "ReceiptEnvelopeSetBuilder",
        "CompilerRunArtifactMaterializer",
        "The receipt coverage builder is compiler-object agnostic.",
        "It must not accept `ValidationReport`, `CommitPreparation`, or `EvidenceRef` as direct inputs.",
        "A compiler-run materializer may read compiler objects and produce artifact material.",
        "The materializer is outside `comp.persistence` and must not mint receipts, discharge requirements, or decide projection authority.",
        "Domain Scenario Lab replay uses the production compiler-run materializer boundary.",
        "Scenario fixture material must remain external material, not builder policy.",
        "## Current Implementation Status",
        "`comp.persistence.envelope_builder`",
        "`build_receipt_envelope_set(...)`",
        "`comp.runtime.compiler_run_artifacts`",
        "`materialize_compiler_run_artifacts(...)`",
        "`ExternalArtifactMaterialSource`",
        "not an authority source",
        "It must not mint receipts, call `build_public_output(...)`, record",
        "Domain Scenario Lab replay must exercise the same path:",
        "must expose it as `ExternalArtifactMaterialSource`",
        "must not recreate `ArtifactEnvelope` construction or receipt-ref coverage",
        "`tests/test_artifact_envelope_builder.py`",
        "`tests/test_compiler_run_artifact_materializer.py`",
    ):
        assert line in builder_doc

    for stale_line in (
        "This document defines the contract for turning a completed compiler run into",
        "The production builder should accept the smallest set that can explain a",
        "compiler-aware materializer remains a later adapter slice",
        "The current Domain Scenario Lab already has a fixture-shaped version",
        "Production code should generalize the materializer contract",
    ):
        assert stale_line not in builder_doc


def test_receipt_proof_graph_contract_names_prework_boundaries():
    graph_doc = Path("docs/architecture/contracts/receipt-proof-graph.md").read_text(
        encoding="utf-8"
    )

    assert "proof_graph" in graph_doc
    assert "dependency_graph" not in graph_doc
    assert "comp.views.receipt_graph" in graph_doc
    assert "MySQLArtifactStore is an ArtifactStore implementation" in graph_doc
    assert "explain_public_field(graph, field=\"co2e_kg\")" in graph_doc
    assert "PublicFieldExplanation" in graph_doc
    assert "`replay_public_projection(...)`, call the projection gate" in graph_doc
    assert "inspect an\n`ArtifactStore`" in graph_doc
    assert "field-level explanations return existing field paths only" in graph_doc


def test_receipt_graph_renderers_have_non_authority_module_boundary():
    from comp.views import receipt_graph

    assert "render-only" in (receipt_graph.__doc__ or "").lower()
    assert "export_receipt_proof_graph" not in receipt_graph.__dict__
    assert "replay_public_projection" not in receipt_graph.__dict__
    assert "build_public_output" not in receipt_graph.__dict__


def test_memory_assisted_loop_documents_agent_core_boundary_contract():
    loop_doc = Path(
        "docs/architecture/contracts/memory-assisted-compiler-loop.md"
    ).read_text(encoding="utf-8")

    assert "## 3.1 Agent Core Boundary Contract" in loop_doc
    for line in (
        "`comp` must not import `minchoagnt`.",
        "`minchoagnt` may import `comp.compiler_tool` report, resolver-task, and fact-adapter contracts.",
        "`minchoagnt` must not import `PublicOutputReceipt`, receipt builders, replay engines, or projection gates.",
        "`CompCompilerAdapter` records report-derived facts and leaves receipt issuance to `comp` governance and receipt paths.",
        "Agent output is proposal and resolution material, not projection authority.",
        "tests/test_authority_import_boundaries.py",
    ):
        assert line in loop_doc


def test_pyproject_packages_comp_core_scenarios_and_agent_layer():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())
    from comp.persistence import (
        ArtifactStore,
        ArtifactEnvelope,
        ArtifactMaterial,
        ArtifactRef,
        InMemoryArtifactStore,
        InMemoryReceiptLedger,
        ProjectionReplayReport,
        ReceiptEnvelopeSetBuildError,
        artifact_digest,
        build_receipt_envelope_set,
        replay_public_projection,
        verify_materialized_public_projection,
    )
    from comp.runtime import (
        CompilerRunArtifactMaterializationError,
        ExternalArtifactMaterial,
        ExternalArtifactMaterialSource,
        TrustRuntime,
        ValidationHandoff,
        ValidationHandoffClaim,
        materialize_compiler_run_artifacts,
    )
    from comp.policy import (
        ConflictResolver,
        DecisionLedger,
        MaterialDescriptor,
        PolicyAssembly,
        PolicyAssemblySubject,
        PolicyDecisionDelta,
        PolicyEffect,
        ScopedGrant,
        SelectionDecision,
        SelectedValidationContract,
        ShadowPolicyComparison,
        policy_artifact_digest,
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
        "comp.policy",
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

    from comp.explanation import (
        PublicFieldExplanation,
        ReceiptProofGraph,
        explain_public_field,
        export_receipt_proof_graph,
    )

    assert ReceiptProofGraph is not None
    assert PublicFieldExplanation is not None
    assert explain_public_field is not None
    assert export_receipt_proof_graph is not None
    assert ArtifactStore is not None
    assert ArtifactEnvelope is not None
    assert ConflictResolver is not None
    assert DecisionLedger is not None
    assert MaterialDescriptor is not None
    assert PolicyAssembly is not None
    assert PolicyAssemblySubject is not None
    assert PolicyDecisionDelta is not None
    assert PolicyEffect is not None
    assert policy_artifact_digest is not None
    assert ScopedGrant is not None
    assert SelectionDecision is not None
    assert SelectedValidationContract is not None
    assert ShadowPolicyComparison is not None
    assert ArtifactMaterial is not None
    assert ArtifactRef is not None
    assert InMemoryArtifactStore is not None
    assert InMemoryReceiptLedger is not None
    assert ProjectionReplayReport is not None
    assert ReceiptEnvelopeSetBuildError is not None
    assert artifact_digest is not None
    assert build_receipt_envelope_set is not None
    assert replay_public_projection is not None
    assert verify_materialized_public_projection is not None
    assert CompilerRunArtifactMaterializationError is not None
    assert ExternalArtifactMaterial is not None
    assert ExternalArtifactMaterialSource is not None
    assert TrustRuntime is not None
    assert ValidationHandoff is not None
    assert ValidationHandoffClaim is not None
    assert materialize_compiler_run_artifacts is not None


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
