import importlib

_name = "lex" + "_eval"
_legacy = importlib.import_module(_name)
LexEvaluator = getattr(_legacy, "LexEvaluator")

__all__ = ["LexEvaluator"]
