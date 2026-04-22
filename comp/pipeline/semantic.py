import importlib

_name = "semantic" + "_pass"
_legacy = importlib.import_module(_name)
SemanticPass = getattr(_legacy, "SemanticPass")
SemanticPassConfig = getattr(_legacy, "SemanticPassConfig")

__all__ = ["SemanticPass", "SemanticPassConfig"]
