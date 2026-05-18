from __future__ import annotations

import pytest

pytest.importorskip("lark")

from tests.fixtures.cases import CASES
from tests.support.builders import run_pipeline_until
from tests.support.serialize import project_result



def test_repair_stage_smoke(load_golden):
    case = next(c for c in CASES if c.name == "happy_path_merge_and_calculate")

    result = run_pipeline_until(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
        pass_name="RepairPass",
    )

    actual = project_result(result)
    expected = load_golden("repair_stage_smoke.json")

    assert actual == expected
