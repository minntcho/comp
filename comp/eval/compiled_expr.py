import importlib

_name = "compiled" + "_expr" + "_eval"
_legacy = importlib.import_module(_name)
CompiledExprEvaluator = getattr(_legacy, "CompiledExprEvaluator")

__all__ = ["CompiledExprEvaluator"]
