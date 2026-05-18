from __future__ import annotations

import pytest

from tests.support.builders import make_resources


def test_make_resources_matches_runner_contract():
    pytest.importorskip("lark")

    from pipeline_runner import PipelineResources

    resources = make_resources()
    assert isinstance(resources, PipelineResources)
    assert hasattr(resources, "llm_fallback")
    assert hasattr(resources, "llm_budget")
