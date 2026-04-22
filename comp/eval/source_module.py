import importlib

_name = "source" + "_eval"
_legacy = importlib.import_module(_name)
SourceEvaluator = getattr(_legacy, "SourceEvaluator")

__all__ = ["SourceEvaluator"]
