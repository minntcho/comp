import importlib

_name = "inference" + "_pass"
_legacy = importlib.import_module(_name)
InferencePass = getattr(_legacy, "InferencePass")

__all__ = ["InferencePass"]
