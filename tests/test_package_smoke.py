from comp import CompiledESGPipelineRunner, ESGPipelineRunner
from comp.compat.artifacts import CompileArtifacts
from comp.compat.compiled_spec import CompiledProgramSpec
from comp.pipeline import LexPass, ParsePass


def test_package_smoke_imports():
    assert ESGPipelineRunner is not None
    assert CompiledESGPipelineRunner is not None
    assert CompileArtifacts is not None
    assert CompiledProgramSpec is not None
    assert LexPass is not None
    assert ParsePass is not None
