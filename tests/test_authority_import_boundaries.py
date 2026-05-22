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
            "comp.scenarios",
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
            "comp.scenarios",
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
)


def test_authority_modules_do_not_import_presentation_or_explanation_layers():
    violations = []
    for rule in AUTHORITY_BOUNDARY_RULES:
        violations.extend(_rule_violations(rule))

    assert violations == []


def test_trust_kernel_contract_documents_machine_checked_import_boundaries():
    contract = Path("docs/architecture/trust-kernel-extension-rings.md").read_text(
        encoding="utf-8"
    )

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


def _is_forbidden(imported: str, rule: ImportBoundaryRule) -> bool:
    if imported in rule.forbidden_imports:
        return True
    return any(
        imported == prefix or imported.startswith(f"{prefix}.")
        for prefix in rule.forbidden_prefixes
    )
