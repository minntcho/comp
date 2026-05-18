from pathlib import Path
import tomllib

import comp
from comp import (
    CommitReceipt,
    Fact,
    FixpointEngine,
    JudgmentState,
    SelectionReceipt,
    SubjectRef,
)


def test_top_level_package_exposes_active_judgment_surface():
    assert Fact is not None
    assert JudgmentState is not None
    assert SubjectRef is not None
    assert FixpointEngine is not None
    assert SelectionReceipt is not None
    assert CommitReceipt is not None


def test_top_level_package_no_longer_exports_legacy_runner_surface():
    assert not hasattr(comp, "ESGPipelineRunner")
    assert not hasattr(comp, "CompiledESGPipelineRunner")
    assert not hasattr(comp, "PipelineResources")
    assert not hasattr(comp, "PipelineRunResult")


def test_pyproject_only_packages_active_surface():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    setuptools_config = pyproject["tool"]["setuptools"]
    assert setuptools_config["packages"] == ["comp", "comp.judgment"]
    assert "py-modules" not in setuptools_config

    dependencies = pyproject["project"].get("dependencies", [])
    assert not any(dependency.startswith("lark") for dependency in dependencies)
