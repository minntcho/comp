import ast
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImportBoundaryRule:
    label: str
    paths: tuple[Path, ...]
    forbidden_prefixes: tuple[str, ...] = ()
    forbidden_imports: tuple[str, ...] = ()


PACKAGE_BOUNDARY_ROLES = {
    "comp": "top-level judgment facade",
    "comp.cli": "outer command adapter",
    "comp.compiler_tool": "compiler authority path",
    "comp.explanation": "explanation-only graph exporter",
    "comp.judgment": "judgment kernel",
    "comp.persistence": "persistence replay path",
    "comp.policy": "pre-validation policy vocabulary",
    "comp.runtime": "scenario runtime adapter",
    "comp.scenario_contracts": "scenario contract harness",
    "comp.scenarios": "minimal scenario package namespace",
    "comp.scenarios.synthetic": "synthetic scenario fixture adapter",
    "comp.views": "render-only view layer",
    "minchoagnt": "agent orchestration layer",
}


EXPECTED_PACKAGE_IMPORTS = {
    "comp": ("comp.judgment",),
    "comp.cli": ("comp.scenario_contracts",),
    "comp.compiler_tool": ("comp.judgment",),
    "comp.explanation": ("comp.judgment", "comp.persistence", "comp.views"),
    "comp.judgment": (),
    "comp.persistence": ("comp.judgment",),
    "comp.policy": (),
    "comp.runtime": (
        "comp.compiler_tool",
        "comp.persistence",
        "comp.scenario_contracts",
    ),
    "comp.scenario_contracts": (
        "comp.judgment",
        "comp.persistence",
        "comp.runtime",
    ),
    "comp.scenarios": (),
    "comp.scenarios.synthetic": ("comp.compiler_tool", "comp.runtime"),
    "comp.views": ("comp", "comp.compiler_tool"),
    "minchoagnt": ("comp.compiler_tool", "comp.judgment"),
}


AUTHORITY_BOUNDARY_RULES = (
    ImportBoundaryRule(
        label="top-level judgment facade",
        paths=(Path("comp/__init__.py"),),
        forbidden_prefixes=(
            "comp.cli",
            "comp.compiler_tool",
            "comp.explanation",
            "comp.persistence",
            "comp.policy",
            "comp.runtime",
            "comp.scenario_contracts",
            "comp.scenarios",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="judgment kernel",
        paths=(Path("comp/judgment"),),
        forbidden_prefixes=(
            "comp.compiler_tool",
            "comp.persistence",
            "comp.explanation",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenario_contracts",
            "comp.scenarios",
            "comp.domains",
            "comp.products",
            "comp.adapters",
            "comp.runtime",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="compiler tool authority path",
        paths=(Path("comp/compiler_tool"),),
        forbidden_prefixes=(
            "comp.persistence",
            "comp.explanation",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenario_contracts",
            "comp.scenarios",
            "comp.domains",
            "comp.products",
            "comp.adapters",
            "comp.runtime",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="persistence replay path",
        paths=(Path("comp/persistence"),),
        forbidden_prefixes=(
            "comp.compiler_tool",
            "comp.explanation",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenarios",
            "comp.runtime",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="policy boundary vocabulary",
        paths=(Path("comp/policy"),),
        forbidden_prefixes=(
            "comp.compiler_tool",
            "comp.judgment",
            "comp.persistence",
            "comp.explanation",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenario_contracts",
            "comp.scenarios",
            "comp.runtime",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="validation handoff bridge",
        paths=(Path("comp/runtime/validation_handoff.py"),),
        forbidden_prefixes=(
            "comp.persistence",
            "comp.explanation",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenario_contracts",
            "comp.scenarios",
            "minchoagnt",
        ),
        forbidden_imports=(
            "comp.compiler_tool:CompilerTool",
            "comp.compiler_tool:CommitPreparation",
            "comp.compiler_tool:ReviewPackage",
            "comp.compiler_tool:PublicOutputReceipt",
            "comp.compiler_tool:build_public_output_receipt",
            "comp.compiler_tool:prepare_commit",
            "comp.persistence:replay_public_projection",
            "comp.persistence.replay:replay_public_projection",
        ),
    ),
    ImportBoundaryRule(
        label="receipt proof graph exporter",
        paths=(Path("comp/explanation/receipt_graph.py"),),
        forbidden_prefixes=(
            "comp.compiler_tool",
            "comp.views",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenarios",
            "comp.runtime",
            "minchoagnt",
        ),
        forbidden_imports=(
            "comp.judgment:build_public_output",
            "comp.persistence:replay_public_projection",
            "comp.persistence.replay:replay_public_projection",
        ),
    ),
    ImportBoundaryRule(
        label="receipt graph renderers",
        paths=(Path("comp/views/receipt_graph.py"),),
        forbidden_prefixes=(
            "comp.compiler_tool",
            "comp.judgment",
            "comp.persistence",
            "comp.explanation",
            "comp.schema_labels",
            "comp.user_messages",
            "comp.scenarios",
            "comp.runtime",
            "minchoagnt",
        ),
    ),
    ImportBoundaryRule(
        label="agent orchestration layer",
        paths=(Path("minchoagnt"),),
        forbidden_prefixes=(
            "comp.explanation",
            "comp.persistence",
            "comp.views",
            "comp.scenario_contracts",
            "comp.scenarios",
            "comp.runtime",
        ),
        forbidden_imports=(
            "comp:PublicOutput",
            "comp:PublicOutputReceipt",
            "comp:PublicOutputSpec",
            "comp:build_public_output",
            "comp.compiler_tool:build_public_output_receipt",
            "comp.compiler_tool:prepare_commit",
            "comp.judgment:PublicOutput",
            "comp.judgment:PublicOutputReceipt",
            "comp.judgment:PublicOutputSpec",
            "comp.judgment:build_public_output",
            "comp.persistence:replay_public_projection",
            "comp.persistence.replay:replay_public_projection",
        ),
    ),
)


def test_top_level_comp_facade_has_machine_checked_boundary():
    labels = {rule.label for rule in AUTHORITY_BOUNDARY_RULES}
    assert "top-level judgment facade" in labels

    contract = Path(
        "docs/architecture/contracts/trust-kernel-extension-rings.md"
    ).read_text(encoding="utf-8")

    expected_lines = (
        "comp top-level package must remain a judgment facade",
        "comp must not import comp.compiler_tool",
        "comp must not import comp.policy",
        "Every packaged surface has an explicit boundary role",
    )
    for line in expected_lines:
        assert line in contract


def test_packaged_surfaces_have_explicit_boundary_roles_documented():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = set(pyproject["tool"]["setuptools"]["packages"])

    assert set(PACKAGE_BOUNDARY_ROLES) == packages

    contract = Path(
        "docs/architecture/contracts/trust-kernel-extension-rings.md"
    ).read_text(encoding="utf-8")
    for package, role in PACKAGE_BOUNDARY_ROLES.items():
        assert f"{package}: {role}" in contract


def test_packaged_surfaces_match_expected_internal_import_snapshot():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    packages = tuple(pyproject["tool"]["setuptools"]["packages"])

    assert set(EXPECTED_PACKAGE_IMPORTS) == set(packages)
    assert _package_import_graph(packages) == EXPECTED_PACKAGE_IMPORTS

    contract = Path(
        "docs/architecture/contracts/trust-kernel-extension-rings.md"
    ).read_text(encoding="utf-8")
    assert "Every packaged surface has a machine-checked import snapshot." in contract
    for package, imports in EXPECTED_PACKAGE_IMPORTS.items():
        expected = ", ".join(imports) if imports else "(none)"
        assert f"{package} -> {expected}" in contract


def test_authority_modules_do_not_import_presentation_or_explanation_layers():
    violations = []
    for rule in AUTHORITY_BOUNDARY_RULES:
        violations.extend(_rule_violations(rule))

    assert violations == []


def test_trust_kernel_contract_documents_machine_checked_import_boundaries():
    contract = Path(
        "docs/architecture/contracts/trust-kernel-extension-rings.md"
    ).read_text(encoding="utf-8")

    expected_lines = (
        "Authority modules cannot import presentation, display, or explanation modules",
        "comp.judgment must not import comp.compiler_tool",
        "comp.compiler_tool must not import comp.persistence",
        "comp.persistence must not import comp.explanation",
        "comp.views.receipt_graph must remain render-only",
        "tests/test_authority_import_boundaries.py",
    )
    for line in expected_lines:
        assert line in contract


def test_compiler_domain_boundary_documents_machine_checked_import_boundaries():
    contract = Path(
        "docs/architecture/contracts/compiler-domain-boundary.md"
    ).read_text(encoding="utf-8")

    expected_lines = (
        "Core code must own protocol, not domain meaning.",
        "DomainPack is a declaration library.",
        "CompilerProfile is the active behavior lock.",
        "Neither is authority.",
        "Core authority modules must not import concrete domain, product, scenario, runtime, or agent packages.",
        "tests/test_authority_import_boundaries.py",
    )
    for line in expected_lines:
        assert line in contract


def test_agent_layer_does_not_call_projection_receipt_or_replay_authority():
    forbidden_calls = {
        "build_public_output",
        "build_public_output_receipt",
        "prepare_commit",
        "replay_public_projection",
        "export_receipt_proof_graph",
        "explain_public_field",
        "InMemoryReceiptLedger",
        "MySQLReceiptLedger",
        "PublicOutputReceipt",
    }
    violations = []
    for source_path in _python_files((Path("minchoagnt"),)):
        for called in _called_names(source_path):
            if called.rsplit(".", 1)[-1] in forbidden_calls:
                violations.append(
                    f"agent orchestration layer: {source_path} calls {called}"
                )

    assert violations == []


def _rule_violations(rule: ImportBoundaryRule) -> list[str]:
    violations = []
    for source_path in _python_files(rule.paths):
        for imported in _imports(source_path):
            if _is_forbidden(imported, rule):
                violations.append(f"{rule.label}: {source_path} imports {imported}")
    return violations


def _python_files(paths: Iterable[Path]) -> tuple[Path, ...]:
    files = []
    for path in paths:
        if path.is_file():
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.rglob("*.py")))
            continue
        raise AssertionError(f"Boundary path does not exist: {path}")
    return tuple(files)


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
            imports.extend(f"{node.module}:{alias.name}" for alias in node.names)
    return tuple(imports)


def _called_names(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            calls.append(_call_name(node.func))
    return tuple(call for call in calls if call)


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        if base:
            return f"{base}.{node.attr}"
        return node.attr
    return ""


def _is_forbidden(imported: str, rule: ImportBoundaryRule) -> bool:
    if imported in rule.forbidden_imports:
        return True
    return any(
        imported == prefix or imported.startswith(f"{prefix}.")
        for prefix in rule.forbidden_prefixes
    )


def _package_import_graph(packages: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    graph = {package: set() for package in packages}
    for source_path in _python_files((Path("comp"), Path("minchoagnt"))):
        source_package = _package_for_path(source_path, packages)
        if source_package is None:
            continue
        for imported in _imports(source_path):
            target_package = _package_for_import(imported.split(":", 1)[0], packages)
            if target_package is not None and target_package != source_package:
                graph[source_package].add(target_package)
    return {
        package: tuple(sorted(imports))
        for package, imports in graph.items()
    }


def _package_for_path(path: Path, packages: tuple[str, ...]) -> str | None:
    module = ".".join(path.with_suffix("").parts)
    return _longest_package_match(module, packages)


def _package_for_import(imported: str, packages: tuple[str, ...]) -> str | None:
    return _longest_package_match(imported, packages)


def _longest_package_match(module: str, packages: tuple[str, ...]) -> str | None:
    matches = tuple(
        package
        for package in packages
        if module == package or module.startswith(f"{package}.")
    )
    if not matches:
        return None
    return max(matches, key=len)
