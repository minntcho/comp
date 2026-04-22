import importlib

_name = "expr" + "_eval"
_legacy = importlib.import_module(_name)
ExprEvaluator = getattr(_legacy, "ExprEvaluator")
EvalContext = getattr(_legacy, "EvalContext")

__all__ = ["ExprEvaluator", "EvalContext"]
