import ast
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ImportBoundaryRule:
    label: str
    paths: tuple[Path, ...]
    forbidden_prefixes: tuple[str, ...] = ()
    forbidden_imports: tuple[str, ...] = ()


AUTHORITY_BOUNDARY_RULES = (
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
