from __future__ import annotations

import pytest

pytest.importorskip("lark")

from compiled_pipeline_runner import CompiledESGPipelineRunner, load_compiled_program_spec_from_dsl
from compiled_spec import CompiledProgramSpec
from pipeline_runner import ESGPipelineRunner
from tests.fixtures.cases import CASES
from tests.support.builders import GRAMMAR_PATH
from tests.support.serialize import project_result


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_compiled_runner_matches_existing_runner(case):
    base_runner = ESGPipelineRunner(grammar_path=GRAMMAR_PATH)
    compiled_runner = CompiledESGPipelineRunner(grammar_path=GRAMMAR_PATH)

    base_result = base_runner.run(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
    )
    compiled_result = compiled_runner.run(
        dsl_text=case.dsl_text,
        fragments=case.fragments,
        resources=case.resources,
    )

    assert project_result(compiled_result) == project_result(base_result)


def test_compiled_loader_returns_compiled_program_spec():
    case = CASES[0]
    compiled_spec = load_compiled_program_spec_from_dsl(
        grammar_path=GRAMMAR_PATH,
        dsl_text=case.dsl_text,
    )

    assert isinstance(compiled_spec, CompiledProgramSpec)
    assert compiled_spec.module_name == "test"
    assert compiled_spec.compiled_constraints
    assert compiled_spec.compiled_resolvers
    assert compiled_spec.compiled_governances
