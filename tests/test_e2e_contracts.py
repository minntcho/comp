from __future__ import annotations

import pytest

pytest.importorskip("lark")

from tests.fixtures.cases import CASES
from tests.support.builders import run_pipeline_full
from tests.support.serialize import project_result


@pytest.mark.e2e
@pytest.mark.golden
@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_e2e_contracts(case, load_golden):
    result = run_pipeline_full(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
    )

    actual = project_result(result)
    expected = load_golden(case.golden_name)
    assert actual == expected
