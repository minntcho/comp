from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def golden_dir() -> Path:
    return Path(__file__).parent / "golden"


@pytest.fixture
def load_golden(golden_dir: Path):
    def _load(name: str):
        path = golden_dir / name
        return json.loads(path.read_text(encoding="utf-8"))

    return _load
